import math

import keras
import numpy as np

import qcflow
from qcflow.keras.callback import QCFlowCallback
from qcflow.tracking.fluent import flush_async_logging


def test_keras_qcflow_callback_log_every_epoch():
    # Prepare data for a 2-class classification.
    data = np.random.uniform(size=(20, 28, 28, 3))
    label = np.random.randint(2, size=20)

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

    num_epochs = 2
    with qcflow.start_run() as run:
        qcflow_callback = QCFlowCallback(log_every_epoch=True)
        model.fit(
            data,
            label,
            validation_data=(data, label),
            batch_size=4,
            epochs=num_epochs,
            callbacks=[qcflow_callback],
        )
    flush_async_logging()
    client = qcflow.QCFlowClient()
    qcflow_run = client.get_run(run.info.run_id)
    run_metrics = qcflow_run.data.metrics
    model_info = qcflow_run.data.params

    assert "sparse_categorical_accuracy" in run_metrics
    assert model_info["optimizer_name"] == "adam"
    assert math.isclose(float(model_info["optimizer_learning_rate"]), 0.001, rel_tol=1e-6)
    assert "loss" in run_metrics
    assert "validation_loss" in run_metrics

    loss_history = client.get_metric_history(run_id=run.info.run_id, key="loss")
    assert len(loss_history) == num_epochs

    validation_loss_history = client.get_metric_history(
        run_id=run.info.run_id,
        key="validation_loss",
    )
    assert len(validation_loss_history) == num_epochs


def test_keras_qcflow_callback_log_every_n_steps():
    # Prepare data for a 2-class classification.
    data = np.random.uniform(size=(20, 28, 28, 3))
    label = np.random.randint(2, size=20)

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

    log_every_n_steps = 1
    num_epochs = 2
    with qcflow.start_run() as run:
        qcflow_callback = QCFlowCallback(log_every_epoch=False, log_every_n_steps=log_every_n_steps)
        model.fit(
            data,
            label,
            validation_data=(data, label),
            batch_size=4,
            epochs=num_epochs,
            callbacks=[qcflow_callback],
        )
    flush_async_logging()
    client = qcflow.QCFlowClient()
    qcflow_run = client.get_run(run.info.run_id)
    run_metrics = qcflow_run.data.metrics
    model_info = qcflow_run.data.params

    assert "sparse_categorical_accuracy" in run_metrics
    assert model_info["optimizer_name"] == "adam"
    assert math.isclose(float(model_info["optimizer_learning_rate"]), 0.001, rel_tol=1e-6)
    assert "loss" in run_metrics
    assert "validation_loss" in run_metrics

    loss_history = client.get_metric_history(run_id=run.info.run_id, key="loss")
    assert len(loss_history) == model.optimizer.iterations.numpy() // log_every_n_steps

    validation_loss_history = client.get_metric_history(
        run_id=run.info.run_id,
        key="validation_loss",
    )
    assert len(validation_loss_history) == num_epochs


def test_old_callback_still_exists():
    assert qcflow.keras.QCFlowCallback is qcflow.keras.QCFlowCallback
