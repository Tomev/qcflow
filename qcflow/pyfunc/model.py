"""
The ``qcflow.pyfunc.model`` module defines logic for saving and loading custom "python_function"
models with a user-defined ``PythonModel`` subclass.
"""

import inspect
import logging
import os
import shutil
import warnings
from abc import ABCMeta, abstractmethod
from pathlib import Path
from typing import Any, Generator, Optional, Union

import cloudpickle
import pandas as pd
import yaml

import qcflow.pyfunc
import qcflow.utils
from qcflow.exceptions import QCFlowException
from qcflow.models import Model
from qcflow.models.model import MLMODEL_FILE_NAME, MODEL_CODE_PATH
from qcflow.models.rag_signatures import ChatCompletionRequest, SplitChatMessagesRequest
from qcflow.models.signature import _extract_type_hints, _is_context_in_predict_function_signature
from qcflow.models.utils import _load_model_code_path
from qcflow.protos.databricks_pb2 import INVALID_PARAMETER_VALUE
from qcflow.pyfunc.utils.input_converter import _hydrate_dataclass
from qcflow.tracking.artifact_utils import _download_artifact_from_uri
from qcflow.types.llm import ChatCompletionChunk, ChatCompletionResponse, ChatMessage, ChatParams
from qcflow.types.utils import _is_list_dict_str, _is_list_str
from qcflow.utils.annotations import experimental
from qcflow.utils.environment import (
    _CONDA_ENV_FILE_NAME,
    _CONSTRAINTS_FILE_NAME,
    _PYTHON_ENV_FILE_NAME,
    _REQUIREMENTS_FILE_NAME,
    _qcflow_conda_env,
    _process_conda_env,
    _process_pip_requirements,
    _PythonEnv,
)
from qcflow.utils.file_utils import TempDir, get_total_file_size, write_to
from qcflow.utils.model_utils import _get_flavor_configuration, _validate_infer_and_copy_code_paths
from qcflow.utils.requirements_utils import _get_pinned_requirement

CONFIG_KEY_ARTIFACTS = "artifacts"
CONFIG_KEY_ARTIFACT_RELATIVE_PATH = "path"
CONFIG_KEY_ARTIFACT_URI = "uri"
CONFIG_KEY_PYTHON_MODEL = "python_model"
CONFIG_KEY_CLOUDPICKLE_VERSION = "cloudpickle_version"
_SAVED_PYTHON_MODEL_SUBPATH = "python_model.pkl"
_DEFAULT_CHAT_MODEL_METADATA_TASK = "agent/v1/chat"
_INVALID_SIGNATURE_ERROR_MSG = (
    "The underlying model's `{func_name}` method contains invalid parameters: {invalid_params}. "
    "Only the following parameter names are allowed: context, model_input, and params. "
    "Note that invalid parameters will no longer be permitted in future versions."
)

_logger = logging.getLogger(__name__)


def get_default_pip_requirements():
    """
    Returns:
        A list of default pip requirements for QCFlow Models produced by this flavor. Calls to
        :func:`save_model()` and :func:`log_model()` produce a pip environment that, at minimum,
        contains these requirements.
    """
    return [_get_pinned_requirement("cloudpickle")]


def get_default_conda_env():
    """
    Returns:
        The default Conda environment for QCFlow Models produced by calls to
        :func:`save_model() <qcflow.pyfunc.save_model>`
        and :func:`log_model() <qcflow.pyfunc.log_model>` when a user-defined subclass of
        :class:`PythonModel` is provided.
    """
    return _qcflow_conda_env(additional_pip_deps=get_default_pip_requirements())


def _log_warning_if_params_not_in_predict_signature(logger, params):
    if params:
        logger.warning(
            "The underlying model does not support passing additional parameters to the predict"
            f" function. `params` {params} will be ignored."
        )


class PythonModel:
    """
    Represents a generic Python model that evaluates inputs and produces API-compatible outputs.
    By subclassing :class:`~PythonModel`, users can create customized QCFlow models with the
    "python_function" ("pyfunc") flavor, leveraging custom inference logic and artifact
    dependencies.
    """

    __metaclass__ = ABCMeta

    def load_context(self, context):
        """
        Loads artifacts from the specified :class:`~PythonModelContext` that can be used by
        :func:`~PythonModel.predict` when evaluating inputs. When loading an QCFlow model with
        :func:`~load_model`, this method is called as soon as the :class:`~PythonModel` is
        constructed.

        The same :class:`~PythonModelContext` will also be available during calls to
        :func:`~PythonModel.predict`, but it may be more efficient to override this method
        and load artifacts from the context at model load time.

        Args:
            context: A :class:`~PythonModelContext` instance containing artifacts that the model
                     can use to perform inference.
        """

    def _get_type_hints(self):
        if _is_context_in_predict_function_signature(func=self.predict):
            return _extract_type_hints(self.predict, input_arg_index=1)
        else:
            return _extract_type_hints(self.predict, input_arg_index=0)

    @abstractmethod
    def predict(self, context, model_input, params: Optional[dict[str, Any]] = None):
        """
        Evaluates a pyfunc-compatible input and produces a pyfunc-compatible output.
        For more information about the pyfunc input/output API, see the :ref:`pyfunc-inference-api`.

        Args:
            context: A :class:`~PythonModelContext` instance containing artifacts that the model
                     can use to perform inference.
            model_input: A pyfunc-compatible input for the model to evaluate.
            params: Additional parameters to pass to the model for inference.

        .. tip::
            Since QCFlow 2.20.0, `context` parameter can be removed from `predict` function
            signature if it's not used. `def predict(self, model_input, params=None)` is valid.
        """

    def predict_stream(self, context, model_input, params: Optional[dict[str, Any]] = None):
        """
        Evaluates a pyfunc-compatible input and produces an iterator of output.
        For more information about the pyfunc input API, see the :ref:`pyfunc-inference-api`.

        Args:
            context: A :class:`~PythonModelContext` instance containing artifacts that the model
                     can use to perform inference.
            model_input: A pyfunc-compatible input for the model to evaluate.
            params: Additional parameters to pass to the model for inference.

        .. tip::
            Since QCFlow 2.20.0, `context` parameter can be removed from `predict_stream` function
            signature if it's not used.
            `def predict_stream(self, model_input, params=None)` is valid.
        """
        raise NotImplementedError()


class _FunctionPythonModel(PythonModel):
    """
    When a user specifies a ``python_model`` argument that is a function, we wrap the function
    in an instance of this class.
    """

    def __init__(self, func, signature=None):
        self.func = func
        self.signature = signature

    def _get_type_hints(self):
        return _extract_type_hints(self.func, input_arg_index=0)

    def predict(
        self,
        model_input,
        params: Optional[dict[str, Any]] = None,
    ):
        """
        Args:
            model_input: A pyfunc-compatible input for the model to evaluate.
            params: Additional parameters to pass to the model for inference.

        Returns:
            Model predictions.
        """
        if "params" in inspect.signature(self.func).parameters:
            return self.func(model_input, params=params)
        _log_warning_if_params_not_in_predict_signature(_logger, params)
        return self.func(model_input)


class PythonModelContext:
    """
    A collection of artifacts that a :class:`~PythonModel` can use when performing inference.
    :class:`~PythonModelContext` objects are created *implicitly* by the
    :func:`save_model() <qcflow.pyfunc.save_model>` and
    :func:`log_model() <qcflow.pyfunc.log_model>` persistence methods, using the contents specified
    by the ``artifacts`` parameter of these methods.
    """

    def __init__(self, artifacts, model_config):
        """
        Args:
            artifacts: A dictionary of ``<name, artifact_path>`` entries, where ``artifact_path``
                is an absolute filesystem path to a given artifact.
            model_config: The model configuration to make available to the model at
                loading time.
        """
        self._artifacts = artifacts
        self._model_config = model_config

    @property
    def artifacts(self):
        """
        A dictionary containing ``<name, artifact_path>`` entries, where ``artifact_path`` is an
        absolute filesystem path to the artifact.
        """
        return self._artifacts

    @experimental
    @property
    def model_config(self):
        """
        A dictionary containing ``<config, value>`` entries, where ``config`` is the name
        of the model configuration keys and ``value`` is the value of the given configuration.
        """

        return self._model_config


@experimental
class ChatModel(PythonModel, metaclass=ABCMeta):
    """
    A subclass of :class:`~PythonModel` that makes it more convenient to implement models
    that are compatible with popular LLM chat APIs. By subclassing :class:`~ChatModel`,
    users can create QCFlow models with a ``predict()`` method that is more convenient
    for chat tasks than the generic :class:`~PythonModel` API. ChatModels automatically
    define input/output signatures and an input example, so manually specifying these values
    when calling :func:`qcflow.pyfunc.save_model() <qcflow.pyfunc.save_model>` is not necessary.

    See the documentation of the ``predict()`` method below for details on that parameters and
    outputs that are expected by the ``ChatModel`` API.
    """

    @abstractmethod
    def predict(
        self, context, messages: list[ChatMessage], params: ChatParams
    ) -> ChatCompletionResponse:
        """
        Evaluates a chat input and produces a chat output.

        Args:
            context: A :class:`~PythonModelContext` instance containing artifacts that the model
                can use to perform inference.
            messages (List[:py:class:`ChatMessage <qcflow.types.llm.ChatMessage>`]):
                A list of :py:class:`ChatMessage <qcflow.types.llm.ChatMessage>`
                objects representing chat history.
            params (:py:class:`ChatParams <qcflow.types.llm.ChatParams>`):
                A :py:class:`ChatParams <qcflow.types.llm.ChatParams>` object
                containing various parameters used to modify model behavior during
                inference.

        .. tip::
            Since QCFlow 2.20.0, `context` parameter can be removed from `predict` function
            signature if it's not used.
            `def predict(self, messages: list[ChatMessage], params: ChatParams)` is valid.

        Returns:
            A :py:class:`ChatCompletionResponse <qcflow.types.llm.ChatCompletionResponse>`
            object containing the model's response(s), as well as other metadata.
        """

    def predict_stream(
        self, context, messages: list[ChatMessage], params: ChatParams
    ) -> Generator[ChatCompletionChunk, None, None]:
        """
        Evaluates a chat input and produces a chat output.
        Override this function to implement a real stream prediction.

        Args:
            context: A :class:`~PythonModelContext` instance containing artifacts that the model
                can use to perform inference.
            messages (List[:py:class:`ChatMessage <qcflow.types.llm.ChatMessage>`]):
                A list of :py:class:`ChatMessage <qcflow.types.llm.ChatMessage>`
                objects representing chat history.
            params (:py:class:`ChatParams <qcflow.types.llm.ChatParams>`):
                A :py:class:`ChatParams <qcflow.types.llm.ChatParams>` object
                containing various parameters used to modify model behavior during
                inference.

        .. tip::
            Since QCFlow 2.20.0, `context` parameter can be removed from `predict_stream` function
            signature if it's not used.
            `def predict_stream(self, messages: list[ChatMessage], params: ChatParams)` is valid.

        Returns:
            A generator over :py:class:`ChatCompletionChunk <qcflow.types.llm.ChatCompletionChunk>`
            object containing the model's response(s), as well as other metadata.
        """
        raise NotImplementedError(
            "Streaming implementation not provided. Please override the "
            "`predict_stream` method on your model to generate streaming "
            "predictions"
        )


def _save_model_with_class_artifacts_params(  # noqa: D417
    path,
    python_model,
    signature=None,
    artifacts=None,
    conda_env=None,
    code_paths=None,
    qcflow_model=None,
    pip_requirements=None,
    extra_pip_requirements=None,
    model_config=None,
    streamable=None,
    model_code_path=None,
    infer_code_paths=False,
):
    """
    Args:
        path: The path to which to save the Python model.
        python_model: An instance of a subclass of :class:`~PythonModel`. ``python_model``
            defines how the model loads artifacts and how it performs inference.
        artifacts: A dictionary containing ``<name, artifact_uri>`` entries. Remote artifact URIs
            are resolved to absolute filesystem paths, producing a dictionary of
            ``<name, absolute_path>`` entries, (e.g. {"file": "absolute_path"}).
            ``python_model`` can reference these resolved entries as the ``artifacts`` property
            of the ``context`` attribute. If ``<artifact_name, 'hf:/repo_id'>``(e.g.
            {"bert-tiny-model": "hf:/prajjwal1/bert-tiny"}) is provided, then the model can be
            fetched from huggingface hub using repo_id `prajjwal1/bert-tiny` directly. If ``None``,
            no artifacts are added to the model.
        conda_env: Either a dictionary representation of a Conda environment or the path to a Conda
            environment yaml file. If provided, this decsribes the environment this model should be
            run in. At minimum, it should specify the dependencies contained in
            :func:`get_default_conda_env()`. If ``None``, the default
            :func:`get_default_conda_env()` environment is added to the model.
        code_paths: A list of local filesystem paths to Python file dependencies (or directories
            containing file dependencies). These files are *prepended* to the system path before the
            model is loaded.
        qcflow_model: The model to which to add the ``qcflow.pyfunc`` flavor.
        model_config: The model configuration for the flavor. Model configuration is available
            during model loading time.

            .. Note:: Experimental: This parameter may change or be removed in a future release
                without warning.

        model_code_path: The path to the code that is being logged as a PyFunc model. Can be used
            to load python_model when python_model is None.

            .. Note:: Experimental: This parameter may change or be removed in a future release
                without warning.

        streamable: A boolean value indicating if the model supports streaming prediction,
                    If None, QCFlow will try to inspect if the model supports streaming
                    by checking if `predict_stream` method exists. Default None.
    """
    if qcflow_model is None:
        qcflow_model = Model()

    custom_model_config_kwargs = {
        CONFIG_KEY_CLOUDPICKLE_VERSION: cloudpickle.__version__,
    }
    if callable(python_model):
        python_model = _FunctionPythonModel(func=python_model, signature=signature)
    saved_python_model_subpath = _SAVED_PYTHON_MODEL_SUBPATH

    # If model_code_path is defined, we load the model into python_model, but we don't want to
    # pickle/save the python_model since the module won't be able to be imported.
    if not model_code_path:
        try:
            with open(os.path.join(path, saved_python_model_subpath), "wb") as out:
                cloudpickle.dump(python_model, out)
        except Exception as e:
            raise QCFlowException(
                "Failed to serialize Python model. Please save the model into a python file "
                "and use code-based logging method instead. See"
                "https://qcflow.org/docs/latest/models.html#models-from-code for more information."
            ) from e

        custom_model_config_kwargs[CONFIG_KEY_PYTHON_MODEL] = saved_python_model_subpath

    if artifacts:
        saved_artifacts_config = {}
        with TempDir() as tmp_artifacts_dir:
            saved_artifacts_dir_subpath = "artifacts"
            hf_prefix = "hf:/"
            for artifact_name, artifact_uri in artifacts.items():
                if artifact_uri.startswith(hf_prefix):
                    try:
                        from huggingface_hub import snapshot_download
                    except ImportError as e:
                        raise QCFlowException(
                            "Failed to import huggingface_hub. Please install huggingface_hub "
                            f"to log the model with artifact_uri {artifact_uri}. Error: {e}"
                        )

                    repo_id = artifact_uri[len(hf_prefix) :]
                    try:
                        snapshot_location = snapshot_download(
                            repo_id=repo_id,
                            local_dir=os.path.join(
                                path, saved_artifacts_dir_subpath, artifact_name
                            ),
                            local_dir_use_symlinks=False,
                        )
                    except Exception as e:
                        raise QCFlowException.invalid_parameter_value(
                            "Failed to download snapshot from Hugging Face Hub with artifact_uri: "
                            f"{artifact_uri}. Error: {e}"
                        )
                    saved_artifact_subpath = (
                        Path(snapshot_location).relative_to(Path(os.path.realpath(path))).as_posix()
                    )
                else:
                    tmp_artifact_path = _download_artifact_from_uri(
                        artifact_uri=artifact_uri, output_path=tmp_artifacts_dir.path()
                    )

                    relative_path = (
                        Path(tmp_artifact_path)
                        .relative_to(Path(tmp_artifacts_dir.path()))
                        .as_posix()
                    )

                    saved_artifact_subpath = os.path.join(
                        saved_artifacts_dir_subpath, relative_path
                    )

                saved_artifacts_config[artifact_name] = {
                    CONFIG_KEY_ARTIFACT_RELATIVE_PATH: saved_artifact_subpath,
                    CONFIG_KEY_ARTIFACT_URI: artifact_uri,
                }

            shutil.move(tmp_artifacts_dir.path(), os.path.join(path, saved_artifacts_dir_subpath))
        custom_model_config_kwargs[CONFIG_KEY_ARTIFACTS] = saved_artifacts_config

    if streamable is None:
        streamable = python_model.__class__.predict_stream != PythonModel.predict_stream

    if model_code_path:
        loader_module = qcflow.pyfunc.loaders.code_model.__name__
    elif python_model:
        loader_module = _get_pyfunc_loader_module(python_model)
    else:
        raise QCFlowException(
            "Either `python_model` or `model_code_path` must be provided to save the model.",
            error_code=INVALID_PARAMETER_VALUE,
        )

    qcflow.pyfunc.add_to_model(
        model=qcflow_model,
        loader_module=loader_module,
        code=None,
        conda_env=_CONDA_ENV_FILE_NAME,
        python_env=_PYTHON_ENV_FILE_NAME,
        model_config=model_config,
        streamable=streamable,
        model_code_path=model_code_path,
        **custom_model_config_kwargs,
    )
    if size := get_total_file_size(path):
        qcflow_model.model_size_bytes = size
    qcflow_model.save(os.path.join(path, MLMODEL_FILE_NAME))

    saved_code_subpath = _validate_infer_and_copy_code_paths(
        code_paths,
        path,
        infer_code_paths,
        qcflow.pyfunc.FLAVOR_NAME,
    )
    qcflow_model.flavors[qcflow.pyfunc.FLAVOR_NAME][qcflow.pyfunc.CODE] = saved_code_subpath

    # `qcflow_model.code` is updated, re-generate `MLmodel` file.
    qcflow_model.save(os.path.join(path, MLMODEL_FILE_NAME))

    if conda_env is None:
        if pip_requirements is None:
            default_reqs = get_default_pip_requirements()
            # To ensure `_load_pyfunc` can successfully load the model during the dependency
            # inference, `qcflow_model.save` must be called beforehand to save an MLmodel file.
            inferred_reqs = qcflow.models.infer_pip_requirements(
                path,
                qcflow.pyfunc.FLAVOR_NAME,
                fallback=default_reqs,
            )
            default_reqs = sorted(set(inferred_reqs).union(default_reqs))
        else:
            default_reqs = None
        conda_env, pip_requirements, pip_constraints = _process_pip_requirements(
            default_reqs,
            pip_requirements,
            extra_pip_requirements,
        )
    else:
        conda_env, pip_requirements, pip_constraints = _process_conda_env(conda_env)

    with open(os.path.join(path, _CONDA_ENV_FILE_NAME), "w") as f:
        yaml.safe_dump(conda_env, stream=f, default_flow_style=False)

    # Save `constraints.txt` if necessary
    if pip_constraints:
        write_to(os.path.join(path, _CONSTRAINTS_FILE_NAME), "\n".join(pip_constraints))

    # Save `requirements.txt`
    write_to(os.path.join(path, _REQUIREMENTS_FILE_NAME), "\n".join(pip_requirements))

    _PythonEnv.current().to_yaml(os.path.join(path, _PYTHON_ENV_FILE_NAME))


def _load_context_model_and_signature(
    model_path: str, model_config: Optional[dict[str, Any]] = None
):
    pyfunc_config = _get_flavor_configuration(
        model_path=model_path, flavor_name=qcflow.pyfunc.FLAVOR_NAME
    )
    signature = qcflow.models.Model.load(model_path).signature

    if MODEL_CODE_PATH in pyfunc_config:
        conf_model_code_path = pyfunc_config.get(MODEL_CODE_PATH)
        model_code_path = os.path.join(model_path, os.path.basename(conf_model_code_path))
        python_model = _load_model_code_path(model_code_path, model_config)

        if callable(python_model):
            python_model = _FunctionPythonModel(python_model, signature=signature)
    else:
        python_model_cloudpickle_version = pyfunc_config.get(CONFIG_KEY_CLOUDPICKLE_VERSION, None)
        if python_model_cloudpickle_version is None:
            qcflow.pyfunc._logger.warning(
                "The version of CloudPickle used to save the model could not be found in the "
                "MLmodel configuration"
            )
        elif python_model_cloudpickle_version != cloudpickle.__version__:
            # CloudPickle does not have a well-defined cross-version compatibility policy. Micro
            # version releases have been known to cause incompatibilities. Therefore, we match on
            # the full library version
            qcflow.pyfunc._logger.warning(
                "The version of CloudPickle that was used to save the model, `CloudPickle %s`, "
                "differs from the version of CloudPickle that is currently running, `CloudPickle "
                "%s`, and may be incompatible",
                python_model_cloudpickle_version,
                cloudpickle.__version__,
            )

        python_model_subpath = pyfunc_config.get(CONFIG_KEY_PYTHON_MODEL, None)
        if python_model_subpath is None:
            raise QCFlowException("Python model path was not specified in the model configuration")
        with open(os.path.join(model_path, python_model_subpath), "rb") as f:
            python_model = cloudpickle.load(f)

    artifacts = {}
    for saved_artifact_name, saved_artifact_info in pyfunc_config.get(
        CONFIG_KEY_ARTIFACTS, {}
    ).items():
        artifacts[saved_artifact_name] = os.path.join(
            model_path, saved_artifact_info[CONFIG_KEY_ARTIFACT_RELATIVE_PATH]
        )

    context = PythonModelContext(artifacts=artifacts, model_config=model_config)
    python_model.load_context(context=context)

    return context, python_model, signature


def _load_pyfunc(model_path: str, model_config: Optional[dict[str, Any]] = None):
    context, python_model, signature = _load_context_model_and_signature(model_path, model_config)
    return _PythonModelPyfuncWrapper(
        python_model=python_model,
        context=context,
        signature=signature,
    )


def _get_first_string_column(pdf):
    iter_string_columns = (col for col, val in pdf.iloc[0].items() if isinstance(val, str))
    return next(iter_string_columns, None)


class _PythonModelPyfuncWrapper:
    """
    Wrapper class that creates a predict function such that
    predict(model_input: pd.DataFrame) -> model's output as pd.DataFrame (pandas DataFrame)
    """

    def __init__(self, python_model: PythonModel, context, signature):
        """
        Args:
            python_model: An instance of a subclass of :class:`~PythonModel`.
            context: A :class:`~PythonModelContext` instance containing artifacts that
                     ``python_model`` may use when performing inference.
            signature: :class:`~ModelSignature` instance describing model input and output.
        """
        self.python_model = python_model
        self.context = context
        self.signature = signature

    def _convert_input(self, model_input):
        import pandas as pd

        hints = self.python_model._get_type_hints()
        # we still need this for backwards compatibility
        if isinstance(model_input, pd.DataFrame):
            if _is_list_str(hints.input):
                first_string_column = _get_first_string_column(model_input)
                if first_string_column is None:
                    raise QCFlowException.invalid_parameter_value(
                        "Expected model input to contain at least one string column"
                    )
                return model_input[first_string_column].tolist()
            elif _is_list_dict_str(hints.input):
                if (
                    len(self.signature.inputs) == 1
                    and next(iter(self.signature.inputs)).name is None
                ):
                    first_string_column = _get_first_string_column(model_input)
                    return model_input[[first_string_column]].to_dict(orient="records")
                return model_input.to_dict(orient="records")
            elif isinstance(hints.input, type) and (
                issubclass(hints.input, ChatCompletionRequest)
                or issubclass(hints.input, SplitChatMessagesRequest)
            ):
                # If the type hint is a RAG dataclass, we hydrate it
                # If there are multiple rows, we should throw
                if len(model_input) > 1:
                    raise QCFlowException(
                        "Expected a single input for dataclass type hint, but got multiple rows"
                    )
                # Since single input is expected, we take the first row
                return _hydrate_dataclass(hints.input, model_input.iloc[0])
        return model_input

    def predict(self, model_input, params: Optional[dict[str, Any]] = None):
        """
        Args:
            model_input: Model input data as one of dict, str, bool, bytes, float, int, str type.
            params: Additional parameters to pass to the model for inference.

        Returns:
            Model predictions as an iterator of chunks. The chunks in the iterator must be type of
            dict or string. Chunk dict fields are determined by the model implementation.
        """
        parameters = inspect.signature(self.python_model.predict).parameters
        if invalid_params := set(parameters) - {"context", "model_input", "params"}:
            warnings.warn(
                _INVALID_SIGNATURE_ERROR_MSG.format(
                    func_name="predict", invalid_params=invalid_params
                ),
                FutureWarning,
                stacklevel=2,
            )
        kwargs = {}
        if "params" in parameters:
            kwargs["params"] = params
        else:
            _log_warning_if_params_not_in_predict_signature(_logger, params)
        if _is_context_in_predict_function_signature(parameters=parameters):
            return self.python_model.predict(
                self.context, self._convert_input(model_input), **kwargs
            )
        else:
            return self.python_model.predict(self._convert_input(model_input), **kwargs)

    def predict_stream(self, model_input, params: Optional[dict[str, Any]] = None):
        """
        Args:
            model_input: LLM Model single input.
            params: Additional parameters to pass to the model for inference.

        Returns:
            Streaming predictions.
        """
        parameters = inspect.signature(self.python_model.predict_stream).parameters
        if invalid_params := set(parameters) - {"context", "model_input", "params"}:
            warnings.warn(
                _INVALID_SIGNATURE_ERROR_MSG.format(
                    func_name="predict_stream", invalid_params=invalid_params
                ),
                FutureWarning,
                stacklevel=2,
            )
        kwargs = {}
        if "params" in parameters:
            kwargs["params"] = params
        else:
            _log_warning_if_params_not_in_predict_signature(_logger, params)
        if _is_context_in_predict_function_signature(parameters=parameters):
            return self.python_model.predict_stream(
                self.context, self._convert_input(model_input), **kwargs
            )
        else:
            return self.python_model.predict_stream(self._convert_input(model_input), **kwargs)


def _get_pyfunc_loader_module(python_model):
    if isinstance(python_model, ChatModel):
        return qcflow.pyfunc.loaders.chat_model.__name__
    return __name__


class ModelFromDeploymentEndpoint(PythonModel):
    """
    A PythonModel wrapper for invoking an QCFlow Deployments endpoint.
    This class is particularly used for running evaluation against an QCFlow Deployments endpoint.
    """

    def __init__(self, endpoint, params):
        self.endpoint = endpoint
        self.params = params

    def predict(
        self, context, model_input: Union[pd.DataFrame, dict[str, Any], list[dict[str, Any]]]
    ):
        """
        Run prediction on the input data.

        Args:
            context: A :class:`~PythonModelContext` instance containing artifacts that the model
                can use to perform inference.
            model_input: The input data for prediction, either of the following:
                - Pandas DataFrame: If the default evaluator is used, input is a DF
                    that contains the multiple request payloads in a single column.
                - A dictionary: If the model_type is "databricks-agents" and the
                    Databricks RAG evaluator is used, this PythonModel can be invoked
                    with a single dict corresponding to the ChatCompletionsRequest schema.
                - A list of dictionaries: Currently we don't have any evaluator that
                    gives this input format, but we keep this for future use cases and
                    compatibility with normal pyfunc models.

        Return:
            The prediction result. The return type will be consistent with the model input type,
            e.g., if the input is a Pandas DataFrame, the return will be a Pandas Series.
        """
        if isinstance(model_input, dict):
            return self._predict_single(model_input)
        elif isinstance(model_input, list) and all(isinstance(data, dict) for data in model_input):
            return [self._predict_single(data) for data in model_input]
        elif isinstance(model_input, pd.DataFrame):
            if len(model_input.columns) != 1:
                raise QCFlowException(
                    f"The number of input columns must be 1, but got {model_input.columns}. "
                    "Multi-column input is not supported for evaluating an QCFlow Deployments "
                    "endpoint. Please include the input text or payload in a single column.",
                    error_code=INVALID_PARAMETER_VALUE,
                )
            input_column = model_input.columns[0]

            predictions = [self._predict_single(data) for data in model_input[input_column]]
            return pd.Series(predictions)
        else:
            raise QCFlowException(
                f"Invalid input data type: {type(model_input)}. The input data must be either "
                "a Pandas DataFrame, a dictionary, or a list of dictionaries containing the "
                "request payloads for evaluating an QCFlow Deployments endpoint.",
                error_code=INVALID_PARAMETER_VALUE,
            )

    def _predict_single(self, data: Union[str, dict[str, Any]]) -> dict[str, Any]:
        """
        Send a single prediction request to the QCFlow Deployments endpoint.

        Args:
            data: The single input data for prediction. If the input data is a string, we will
                construct the request payload from it. If the input data is a dictionary, we
                will directly use it as the request payload.

        Returns:
            The prediction result from the QCFlow Deployments endpoint as a dictionary.
        """
        from qcflow.metrics.genai.model_utils import call_deployments_api, get_endpoint_type

        endpoint_type = get_endpoint_type(f"endpoints:/{self.endpoint}")

        if isinstance(data, str):
            # If the input payload is string, QCFlow needs to construct the JSON
            # payload based on the endpoint type. If the endpoint type is not
            # set on the endpoint, we will default to chat format.
            endpoint_type = endpoint_type or "llm/v1/chat"
            prediction = call_deployments_api(self.endpoint, data, self.params, endpoint_type)
        elif isinstance(data, dict):
            # If the input is dictionary, we assume the input is already in the
            # compatible format for the endpoint.
            prediction = call_deployments_api(self.endpoint, data, self.params, endpoint_type)
        else:
            raise QCFlowException(
                f"Invalid input data type: {type(data)}. The feature column of the evaluation "
                "dataset must contain only strings or dictionaries containing the request "
                "payload for evaluating an QCFlow Deployments endpoint.",
                error_code=INVALID_PARAMETER_VALUE,
            )
        return prediction
