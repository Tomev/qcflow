"""
The ``qcflow.models`` module provides an API for saving machine learning models in
"flavors" that can be understood by different downstream tools.

The built-in flavors are:

- :py:mod:`qcflow.catboost`
- :py:mod:`qcflow.diviner`
- :py:mod:`qcflow.dspy`
- :py:mod:`qcflow.fastai`
- :py:mod:`qcflow.h2o`
- :py:mod:`qcflow.langchain`
- :py:mod:`qcflow.lightgbm`
- :py:mod:`qcflow.llama_index`
- :py:mod:`qcflow.mleap`
- :py:mod:`qcflow.onnx`
- :py:mod:`qcflow.openai`
- :py:mod:`qcflow.paddle`
- :py:mod:`qcflow.pmdarima`
- :py:mod:`qcflow.prophet`
- :py:mod:`qcflow.pyfunc`
- :py:mod:`qcflow.pyspark.ml`
- :py:mod:`qcflow.pytorch`
- :py:mod:`qcflow.sklearn`
- :py:mod:`qcflow.spacy`
- :py:mod:`qcflow.spark`
- :py:mod:`qcflow.statsmodels`
- :py:mod:`qcflow.tensorflow`
- :py:mod:`qcflow.transformers`
- :py:mod:`qcflow.xgboost`

For details, see `QCFlow Models <../models.html>`_.
"""

from qcflow.models.dependencies_schemas import set_retriever_schema
from qcflow.models.evaluation import (
    EvaluationArtifact,
    EvaluationMetric,
    EvaluationResult,
    MetricThreshold,
    evaluate,
    list_evaluators,
    make_metric,
)
from qcflow.models.flavor_backend import FlavorBackend
from qcflow.models.model import Model, get_model_info, set_model, update_model_requirements
from qcflow.models.model_config import ModelConfig
from qcflow.models.python_api import build_docker
from qcflow.models.resources import Resource, ResourceType
from qcflow.utils.environment import infer_pip_requirements

__all__ = [
    "Model",
    "FlavorBackend",
    "infer_pip_requirements",
    "evaluate",
    "make_metric",
    "EvaluationMetric",
    "EvaluationArtifact",
    "EvaluationResult",
    "get_model_info",
    "set_model",
    "set_retriever_schema",
    "list_evaluators",
    "MetricThreshold",
    "build_docker",
    "Resource",
    "ResourceType",
    "ModelConfig",
    "update_model_requirements",
]


# Under skinny-qcflow requirements, the following packages cannot be imported
# because of lack of numpy/pandas library, so wrap them with try...except block
try:
    from qcflow.models.python_api import predict
    from qcflow.models.signature import ModelSignature, infer_signature, set_signature
    from qcflow.models.utils import (
        ModelInputExample,
        add_libraries_to_model,
        convert_input_example_to_serving_input,
        validate_schema,
        validate_serving_input,
    )

    __all__ += [
        "ModelSignature",
        "ModelInputExample",
        "infer_signature",
        "validate_schema",
        "add_libraries_to_model",
        "convert_input_example_to_serving_input",
        "set_signature",
        "predict",
        "validate_serving_input",
    ]
except ImportError:
    pass
