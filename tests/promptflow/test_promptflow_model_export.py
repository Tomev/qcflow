from pathlib import Path

import pytest
from promptflow import load_flow
from pyspark.sql import SparkSession

import qcflow
from qcflow import QCFlowException
from qcflow.deployments import PredictionsResponse
from qcflow.models.utils import load_serving_example
from qcflow.pyfunc.scoring_server import CONTENT_TYPE_JSON

from tests.helper_functions import pyfunc_serve_and_score_model


@pytest.fixture(scope="module")
def spark():
    with SparkSession.builder.master("local[*]").getOrCreate() as s:
        yield s


def get_promptflow_example_model():
    flow_path = Path(__file__).parent / "flow_with_additional_includes"
    return load_flow(flow_path)


def test_promptflow_log_and_load_model():
    logged_model = log_promptflow_example_model(with_input_example=True)
    qcflow.promptflow.load_model(logged_model.model_uri)

    assert "promptflow" in logged_model.flavors
    assert logged_model.signature is not None
    assert logged_model.signature.inputs.to_dict() == [
        {"name": "text", "type": "string", "required": True}
    ]
    assert logged_model.signature.outputs.to_dict() == [
        {"name": "output", "type": "string", "required": True}
    ]


def test_log_model_with_config():
    model = get_promptflow_example_model()
    model_config = {
        "connection_provider": "local",
        "connection_overrides": {"local_connection_name": "remote_connection_name"},
    }
    with qcflow.start_run():
        logged_model = qcflow.promptflow.log_model(
            model, "promptflow_model", model_config=model_config
        )

    assert qcflow.pyfunc.FLAVOR_NAME in logged_model.flavors
    assert qcflow.pyfunc.MODEL_CONFIG in logged_model.flavors[qcflow.pyfunc.FLAVOR_NAME]
    logged_model_config = logged_model.flavors[qcflow.pyfunc.FLAVOR_NAME][
        qcflow.pyfunc.MODEL_CONFIG
    ]
    assert logged_model_config == model_config


def log_promptflow_example_model(with_input_example=False):
    model = get_promptflow_example_model()
    with qcflow.start_run():
        if not with_input_example:
            return qcflow.promptflow.log_model(model, "promptflow_model")
        return qcflow.promptflow.log_model(
            model,
            "promptflow_model",
            input_example={"text": "Python Hello World!"},
        )


def test_promptflow_model_predict_pyfunc():
    logged_model = log_promptflow_example_model()
    loaded_model = qcflow.pyfunc.load_model(logged_model.model_uri)
    # Assert pyfunc model
    assert "promptflow" in logged_model.flavors
    assert type(loaded_model) == qcflow.pyfunc.PyFuncModel
    # Assert predict with pyfunc model
    input_value = "Python Hello World!"
    result = loaded_model.predict({"text": input_value})
    expected_result = (
        "system:\nYour task is to generate what I ask.\nuser:\n"
        f"Write a simple {input_value} program that displays the greeting message."
    )
    assert result == {"output": expected_result}


def test_promptflow_model_serve_predict():
    # Assert predict with promptflow model
    logged_model = log_promptflow_example_model(with_input_example=True)
    inference_payload = load_serving_example(logged_model.model_uri)
    response = pyfunc_serve_and_score_model(
        logged_model.model_uri,
        data=inference_payload,
        content_type=CONTENT_TYPE_JSON,
        extra_args=["--env-manager", "local"],
    )
    expected_result = (
        "system:\nYour task is to generate what I ask.\nuser:\n"
        "Write a simple Python Hello World! program that displays the "
        "greeting message."
    )
    assert PredictionsResponse.from_json(response.content.decode("utf-8")) == {
        "predictions": [{"output": expected_result}]
    }


def test_promptflow_model_sparkudf_predict(spark):
    # Assert predict with promptflow model
    logged_model = log_promptflow_example_model(with_input_example=True)
    # Assert predict with spark udf
    udf = qcflow.pyfunc.spark_udf(
        spark,
        logged_model.model_uri,
        result_type="string",
    )
    input_value = "Python Hello World!"
    df = spark.createDataFrame([(input_value,)], ["text"])
    df = df.withColumn("outputs", udf("text"))
    pdf = df.toPandas()
    expected_result = (
        "system:\nYour task is to generate what I ask.\nuser:\n"
        f"Write a simple {input_value} program that displays the greeting message."
    )
    assert pdf["outputs"].tolist() == [expected_result]


def test_unsupported_class():
    mock_model = object()
    with pytest.raises(
        QCFlowException, match="only supports instance defined with 'flow.dag.yaml' file"
    ):
        with qcflow.start_run():
            qcflow.promptflow.log_model(mock_model, "mock_model_path")
