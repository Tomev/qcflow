import json
import math
import os

import keras
import numpy as np
import pytest
import yaml

import qcflow
from qcflow import QCFlowClient
from qcflow.tracking.fluent import flush_async_logging
from qcflow.types import Schema, TensorSpec
from qcflow.utils.autologging_utils import AUTOLOGGING_INTEGRATIONS


@pytest.fixture(autouse=True)
def clear_autologging_config():
    yield
    AUTOLOGGING_INTEGRATIONS.pop("keras", None)


def _create_keras_model():
    model = keras.Sequential(
        [
            keras.Input([28, 28, 3]),
            keras.layers.Flatten(),
            keras.layers.Dense(2),
        ]
    )

    model.compile(
        loss=keras.losses.SparseCategoricalCrossentropy(from_logits=True),
        optimizer=keras.optimizers.Adam(0.001),
        metrics=[keras.metrics.SparseCategoricalAccuracy()],
    )
    return model


def _check_logged_model_signature_is_expected(run, input_schema, output_schema):
    artifacts_dir = run.info.artifact_uri.replace("file://", "")
    client = QCFlowClient()
    artifacts = [x.path for x in client.list_artifacts(run.info.run_id, "model")]
    ml_model_filename = "MLmodel"
    assert str(os.path.join("model", ml_model_filename)) in artifacts
    ml_model_path = os.path.join(artifacts_dir, "model", ml_model_filename)
    with open(ml_model_path) as f:
        model_config = yaml.load(f, Loader=yaml.FullLoader)
        assert model_config is not None
        assert "signature" in model_config
        signature = model_config["signature"]
        assert signature is not None
        assert "inputs" in signature
        assert "outputs" in signature
        assert signature["inputs"] == input_schema.to_json()
        assert signature["outputs"] == output_schema.to_json()


def test_default_autolog_behavior():
    qcflow.keras.autolog()

    # Prepare data for a 2-class classification.
    data = np.random.uniform(size=(20, 28, 28, 3))
    label = np.random.randint(2, size=20)

    model = _create_keras_model()

    num_epochs = 2
    batch_size = 4
    with qcflow.start_run() as run:
        model.fit(
            data,
            label,
            validation_data=(data, label),
            batch_size=batch_size,
            epochs=num_epochs,
        )
    flush_async_logging()
    client = qcflow.QCFlowClient()
    qcflow_run = client.get_run(run.info.run_id)
    run_metrics = qcflow_run.data.metrics
    model_info = qcflow_run.data.params

    # Assert training configs are logged correctly.
    assert int(model_info["batch_size"]) == batch_size
    assert model_info["optimizer_name"] == "adam"
    assert math.isclose(float(model_info["optimizer_learning_rate"]), 0.001, rel_tol=1e-6)

    assert "loss" in run_metrics
    assert "sparse_categorical_accuracy" in run_metrics
    assert "validation_loss" in run_metrics

    # Assert metrics are logged in the correct number of times.
    loss_history = client.get_metric_history(run_id=run.info.run_id, key="loss")
    assert len(loss_history) == num_epochs

    validation_loss_history = client.get_metric_history(
        run_id=run.info.run_id,
        key="validation_loss",
    )
    assert len(validation_loss_history) == num_epochs

    # Test the loaded pyfunc model produces the same output for the same input as the model.
    test_input = np.random.uniform(size=[2, 28, 28, 3]).astype(np.float32)
    logged_model = f"runs:/{run.info.run_id}/model"
    loaded_pyfunc_model = qcflow.pyfunc.load_model(logged_model)
    np.testing.assert_allclose(
        keras.ops.convert_to_numpy(model(test_input)),
        loaded_pyfunc_model.predict(test_input),
    )

    # Test the signature is logged.
    input_schema = Schema([TensorSpec(np.dtype(np.float32), (-1, 28, 28, 3))])
    output_schema = Schema([TensorSpec(np.dtype(np.float32), (-1, 2))])
    _check_logged_model_signature_is_expected(run, input_schema, output_schema)


@pytest.mark.parametrize(
    (
        "log_every_epoch",
        "log_every_n_steps",
        "log_models",
        "log_model_signatures",
        "save_exported_model",
    ),
    [
        (False, 1, False, False, False),
        (False, 2, True, True, True),
        (True, None, False, False, False),
    ],
)
def test_custom_autolog_behavior(
    log_every_epoch,
    log_every_n_steps,
    log_models,
    log_model_signatures,
    save_exported_model,
):
    if keras.backend.backend() != "tensorflow" and save_exported_model:
        pytest.skip("Only TensorFlow backend supports saving exported models.")
    qcflow.keras.autolog(
        log_every_epoch=log_every_epoch,
        log_every_n_steps=log_every_n_steps,
        log_models=log_models,
        log_model_signatures=log_model_signatures,
        save_exported_model=save_exported_model,
    )

    # Prepare data for a 2-class classification.
    data = np.random.uniform(size=(20, 28, 28, 3))
    label = np.random.randint(2, size=20)

    model = _create_keras_model()

    num_epochs = 1
    batch_size = 4
    with qcflow.start_run() as run:
        model.fit(
            data,
            label,
            validation_data=(data, label),
            batch_size=batch_size,
            epochs=num_epochs,
        )
    flush_async_logging()
    client = qcflow.QCFlowClient()
    qcflow_run = client.get_run(run.info.run_id)
    run_metrics = qcflow_run.data.metrics
    model_info = qcflow_run.data.params

    # Assert training configs are logged correctly.
    assert int(model_info["batch_size"]) == batch_size
    assert model_info["optimizer_name"] == "adam"
    assert math.isclose(float(model_info["optimizer_learning_rate"]), 0.001, rel_tol=1e-6)

    assert "loss" in run_metrics
    assert "sparse_categorical_accuracy" in run_metrics
    assert "validation_loss" in run_metrics

    # Assert metrics are logged in the correct number of times.
    loss_history = client.get_metric_history(run_id=run.info.run_id, key="loss")
    if log_every_n_steps:
        metric_length = model.optimizer.iterations.numpy() // log_every_n_steps
    else:
        metric_length = num_epochs
    assert len(loss_history) == metric_length

    validation_loss_history = client.get_metric_history(
        run_id=run.info.run_id,
        key="validation_loss",
    )
    assert len(validation_loss_history) == num_epochs

    if not log_models:
        # Test the model is not logged.
        assert "qcflow.log-model.history" not in qcflow_run.data.tags


@pytest.mark.parametrize("log_datasets", [True, False])
def test_keras_autolog_log_datasets(log_datasets):
    qcflow.keras.autolog(log_datasets=log_datasets)

    # Prepare data for a 2-class classification.
    data = np.random.uniform(size=(20, 28, 28, 3)).astype(np.float32)
    label = np.random.randint(2, size=20)

    model = _create_keras_model()

    model.fit(data, label, epochs=2)
    flush_async_logging()
    client = qcflow.QCFlowClient()
    dataset_inputs = client.get_run(qcflow.last_active_run().info.run_id).inputs.dataset_inputs
    if log_datasets:
        assert len(dataset_inputs) == 1
        feature_schema = Schema(
            [
                TensorSpec(np.dtype(np.float32), (-1, 28, 28, 3)),
            ]
        )
        target_schema = Schema(
            [
                TensorSpec(np.dtype(np.int64), (-1,)),
            ]
        )
        expected = json.dumps(
            {
                "qcflow_tensorspec": {
                    "features": feature_schema.to_json(),
                    "targets": target_schema.to_json(),
                }
            }
        )
        assert dataset_inputs[0].dataset.schema == expected
    else:
        assert len(dataset_inputs) == 0
