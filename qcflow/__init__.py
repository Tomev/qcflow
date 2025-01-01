"""
The ``qcflow`` module provides a high-level "fluent" API for starting and managing QCFlow runs.
For example:

.. code:: python

    import qcflow

    qcflow.start_run()
    qcflow.log_param("my", "param")
    qcflow.log_metric("score", 100)
    qcflow.end_run()

You can also use the context manager syntax like this:

.. code:: python

    with qcflow.start_run() as run:
        qcflow.log_param("my", "param")
        qcflow.log_metric("score", 100)

which automatically terminates the run at the end of the ``with`` block.

The fluent tracking API is not currently threadsafe. Any concurrent callers to the tracking API must
implement mutual exclusion manually.

For a lower level API, see the :py:mod:`qcflow.client` module.
"""

import contextlib

from qcflow.version import VERSION

__version__ = VERSION
from qcflow import (
    artifacts,  # noqa: F401
    client,  # noqa: F401
    config,  # noqa: F401
    data,  # noqa: F401
    exceptions,  # noqa: F401
    models,  # noqa: F401
    projects,  # noqa: F401
    tracing,  # noqa: F401
    tracking,  # noqa: F401
)
from qcflow.environment_variables import QCFLOW_CONFIGURE_LOGGING
from qcflow.utils.lazy_load import LazyLoader
from qcflow.utils.logging_utils import _configure_qcflow_loggers

# Lazily load qcflow flavors to avoid excessive dependencies.
anthropic = LazyLoader("qcflow.anthropic", globals(), "qcflow.anthropic")
autogen = LazyLoader("qcflow.autogen", globals(), "qcflow.autogen")
bedrock = LazyLoader("qcflow.bedrock", globals(), "qcflow.bedrock")
catboost = LazyLoader("qcflow.catboost", globals(), "qcflow.catboost")
crewai = LazyLoader("qcflow.crewai", globals(), "qcflow.crewai")
diviner = LazyLoader("qcflow.diviner", globals(), "qcflow.diviner")
dspy = LazyLoader("qcflow.dspy", globals(), "qcflow.dspy")
fastai = LazyLoader("qcflow.fastai", globals(), "qcflow.fastai")
gemini = LazyLoader("qcflow.gemini", globals(), "qcflow.gemini")
h2o = LazyLoader("qcflow.h2o", globals(), "qcflow.h2o")
johnsnowlabs = LazyLoader("qcflow.johnsnowlabs", globals(), "qcflow.johnsnowlabs")
keras = LazyLoader("qcflow.keras", globals(), "qcflow.keras")
langchain = LazyLoader("qcflow.langchain", globals(), "qcflow.langchain")
lightgbm = LazyLoader("qcflow.lightgbm", globals(), "qcflow.lightgbm")
litellm = LazyLoader("qcflow.litellm", globals(), "qcflow.litellm")
llama_index = LazyLoader("qcflow.llama_index", globals(), "qcflow.llama_index")
llm = LazyLoader("qcflow.llm", globals(), "qcflow.llm")
metrics = LazyLoader("qcflow.metrics", globals(), "qcflow.metrics")
mleap = LazyLoader("qcflow.mleap", globals(), "qcflow.mleap")
onnx = LazyLoader("qcflow.onnx", globals(), "qcflow.onnx")
openai = LazyLoader("qcflow.openai", globals(), "qcflow.openai")
paddle = LazyLoader("qcflow.paddle", globals(), "qcflow.paddle")
pmdarima = LazyLoader("qcflow.pmdarima", globals(), "qcflow.pmdarima")
promptflow = LazyLoader("qcflow.promptflow", globals(), "qcflow.promptflow")
prophet = LazyLoader("qcflow.prophet", globals(), "qcflow.prophet")
promptlab = LazyLoader("qcflow.promptlab", globals(), "qcflow.promptlab")
pyfunc = LazyLoader("qcflow.pyfunc", globals(), "qcflow.pyfunc")
pyspark = LazyLoader("qcflow.pyspark", globals(), "qcflow.pyspark")
pytorch = LazyLoader("qcflow.pytorch", globals(), "qcflow.pytorch")
rfunc = LazyLoader("qcflow.rfunc", globals(), "qcflow.rfunc")
recipes = LazyLoader("qcflow.recipes", globals(), "qcflow.recipes")
sentence_transformers = LazyLoader(
    "qcflow.sentence_transformers",
    globals(),
    "qcflow.sentence_transformers",
)
shap = LazyLoader("qcflow.shap", globals(), "qcflow.shap")
sklearn = LazyLoader("qcflow.sklearn", globals(), "qcflow.sklearn")
spacy = LazyLoader("qcflow.spacy", globals(), "qcflow.spacy")
spark = LazyLoader("qcflow.spark", globals(), "qcflow.spark")
statsmodels = LazyLoader("qcflow.statsmodels", globals(), "qcflow.statsmodels")
tensorflow = LazyLoader("qcflow.tensorflow", globals(), "qcflow.tensorflow")
transformers = LazyLoader("qcflow.transformers", globals(), "qcflow.transformers")
xgboost = LazyLoader("qcflow.xgboost", globals(), "qcflow.xgboost")

if QCFLOW_CONFIGURE_LOGGING.get() is True:
    _configure_qcflow_loggers(root_module_name=__name__)

from qcflow.client import QCFlowClient

# For backward compatibility, we expose the following functions and classes at the top level in
# addition to `qcflow.config`.
from qcflow.config import (
    disable_system_metrics_logging,
    enable_system_metrics_logging,
    get_registry_uri,
    get_tracking_uri,
    is_tracking_uri_set,
    set_registry_uri,
    set_system_metrics_node_id,
    set_system_metrics_samples_before_logging,
    set_system_metrics_sampling_interval,
    set_tracking_uri,
)
from qcflow.exceptions import QCFlowException
from qcflow.models import evaluate
from qcflow.models.evaluation.validation import validate_evaluation_results
from qcflow.projects import run
from qcflow.tracing.fluent import (
    add_trace,
    get_current_active_span,
    get_last_active_trace,
    get_trace,
    search_traces,
    start_span,
    trace,
    update_current_trace,
)
from qcflow.tracking._model_registry.fluent import (
    register_model,
    search_model_versions,
    search_registered_models,
)
from qcflow.tracking.fluent import (
    ActiveRun,
    active_run,
    autolog,
    create_experiment,
    delete_experiment,
    delete_run,
    delete_tag,
    end_run,
    flush_artifact_async_logging,
    flush_async_logging,
    flush_trace_async_logging,
    get_artifact_uri,
    get_experiment,
    get_experiment_by_name,
    get_parent_run,
    get_run,
    last_active_run,
    load_table,
    log_artifact,
    log_artifacts,
    log_dict,
    log_figure,
    log_image,
    log_input,
    log_metric,
    log_metrics,
    log_param,
    log_params,
    log_table,
    log_text,
    search_experiments,
    search_runs,
    set_experiment,
    set_experiment_tag,
    set_experiment_tags,
    set_tag,
    set_tags,
    start_run,
)
from qcflow.tracking.multimedia import Image
from qcflow.utils.async_logging.run_operations import RunOperations  # noqa: F401
from qcflow.utils.credentials import login
from qcflow.utils.doctor import doctor

__all__ = [
    "ActiveRun",
    "QCFlowClient",
    "QCFlowException",
    "active_run",
    "autolog",
    "create_experiment",
    "delete_experiment",
    "delete_run",
    "delete_tag",
    "disable_system_metrics_logging",
    "doctor",
    "enable_system_metrics_logging",
    "end_run",
    "evaluate",
    "flush_async_logging",
    "flush_artifact_async_logging",
    "flush_trace_async_logging",
    "get_artifact_uri",
    "get_experiment",
    "get_experiment_by_name",
    "get_last_active_trace",
    "get_parent_run",
    "get_registry_uri",
    "get_run",
    "get_tracking_uri",
    "is_tracking_uri_set",
    "last_active_run",
    "load_table",
    "log_artifact",
    "log_artifacts",
    "log_dict",
    "log_figure",
    "log_image",
    "log_input",
    "log_metric",
    "log_metrics",
    "log_param",
    "log_params",
    "log_table",
    "log_text",
    "login",
    "pyfunc",
    "register_model",
    "run",
    "search_experiments",
    "search_model_versions",
    "search_registered_models",
    "search_runs",
    "set_experiment",
    "set_experiment_tag",
    "set_experiment_tags",
    "set_registry_uri",
    "set_system_metrics_node_id",
    "set_system_metrics_samples_before_logging",
    "set_system_metrics_sampling_interval",
    "set_tag",
    "set_tags",
    "set_tracking_uri",
    "start_run",
    "validate_evaluation_results",
    "Image",
    # Tracing Fluent APIs
    "get_current_active_span",
    "get_trace",
    "search_traces",
    "start_span",
    "trace",
    "add_trace",
    "update_current_trace",
]


# `qcflow.gateway` depends on optional dependencies such as pydantic, psutil, and has version
# restrictions for dependencies. Importing this module fails if they are not installed or
# if invalid versions of these required packages are installed.
with contextlib.suppress(Exception):
    from qcflow import gateway  # noqa: F401

    __all__.append("gateway")
