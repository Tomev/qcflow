import io
import pickle
import time
import uuid

import pytest

import qcflow
from qcflow import QCFlowClient
from qcflow.entities.metric import Metric
from qcflow.entities.param import Param
from qcflow.entities.run_tag import RunTag


@pytest.fixture(autouse=True)
def flush_async_logging():
    """Flush async logging after each test to avoid interference between tests"""
    yield
    qcflow.flush_async_logging()


def test_async_logging_qcflow_client_pickle():
    experiment_name = f"qcflow-async-logging-pickle-test-{str(uuid.uuid4())[:8]}"
    qcflow_client = QCFlowClient()

    buffer = io.BytesIO()
    pickle.dump(qcflow_client, buffer)

    deserialized_qcflow_client = pickle.loads(buffer.getvalue())  # Type: QCFlowClient
    experiment_id = deserialized_qcflow_client.create_experiment(experiment_name)

    run = deserialized_qcflow_client.create_run(experiment_id=experiment_id)
    run_id = run.info.run_id

    run_operations = []

    params_to_log = []
    param1 = Param("async param 1", "async param 1 value")
    run_operations.append(
        qcflow_client.log_param(run_id, param1.key, param1.value, synchronous=False)
    )
    params_to_log.append(param1)

    for run_operation in run_operations:
        run_operation.wait()
    run = qcflow_client.get_run(run_id)
    assert param1.key in run.data.params
    assert param1.value == run.data.params[param1.key]


def test_async_logging_qcflow_client():
    experiment_name = f"qcflow-async-logging-test-{str(uuid.uuid4())[:8]}"
    qcflow_client = QCFlowClient()
    experiment_id = qcflow_client.create_experiment(experiment_name)

    run = qcflow_client.create_run(experiment_id=experiment_id)
    run_id = run.info.run_id

    run_operations = []

    params_to_log = []
    param1 = Param("async param 1", "async param 1 value")
    run_operations.append(
        qcflow_client.log_param(run_id, param1.key, param1.value, synchronous=False)
    )
    params_to_log.append(param1)

    tags_to_log = []
    tag1 = RunTag("async tag 1", "async tag 1 value")
    run_operations.append(qcflow_client.set_tag(run_id, tag1.key, tag1.value, synchronous=False))
    tags_to_log.append(tag1)

    metrics_to_log = []
    metric1 = Metric("async metric 1", 1, 132, 0)
    run_operations.append(
        qcflow_client.log_metric(
            run_id, metric1.key, metric1.value, metric1.timestamp, metric1.step, synchronous=False
        )
    )
    metrics_to_log.append(metric1)

    # Log batch of metrics
    metric_value = 1
    for _ in range(1, 5):
        metrics = []
        guid8 = str(uuid.uuid4())[:8]
        params = [Param(f"batch param-{guid8}-{val}", value=str(val)) for val in range(1)]
        tags = [RunTag(f"batch tag-{guid8}-{val}", value=str(val)) for val in range(1)]
        for _ in range(0, 50):
            metric_value += 1
            metrics.append(
                Metric(
                    key=f"batch metrics async-{metric_value}",
                    value=time.time(),
                    timestamp=metric_value,
                    step=0,
                )
            )

        params_to_log.extend(params)
        tags_to_log.extend(tags)
        metrics_to_log.extend(metrics)
        run_operation = qcflow_client.log_batch(
            run_id,
            params=params,
            tags=tags,
            metrics=metrics,
            synchronous=False,
        )
        run_operations.append(run_operation)

    # Terminate the run before async operations are completed
    # The remaining operations should still be processed
    qcflow_client.set_terminated(run_id=run_id, status="FINISHED", end_time=time.time())

    for run_operation in run_operations:
        run_operation.wait()

    run = qcflow_client.get_run(run_id)
    for tag in tags_to_log:
        assert tag.key in run.data.tags
        assert tag.value == run.data.tags[tag.key]
    for param in params_to_log:
        assert param.key in run.data.params
        assert param.value == run.data.params[param.key]
    for metric in metrics_to_log:
        assert metric.key in run.data.metrics
        assert metric.value == run.data.metrics[metric.key]


def test_async_logging_fluent():
    experiment_name = f"qcflow-async-logging-test-{str(uuid.uuid4())[:8]}"
    experiment_id = qcflow.create_experiment(experiment_name)

    run_operations = []

    with qcflow.start_run(experiment_id=experiment_id) as run:
        run_id = run.info.run_id
        params_to_log = []
        param1 = Param("async param 1", "async param 1 value")
        run_operations.append(qcflow.log_param(param1.key, param1.value, synchronous=False))
        params_to_log.append(param1)

        tags_to_log = []
        tag1 = RunTag("async tag 1", "async tag 1 value")
        run_operations.append(qcflow.set_tag(tag1.key, tag1.value, synchronous=False))
        tags_to_log.append(tag1)

        metrics_to_log = []
        metric1 = Metric("async metric 1", 1, 432, 0)
        run_operations.append(qcflow.log_metric(metric1.key, metric1.value, synchronous=False))
        metrics_to_log.append(metric1)

        # Log batch of metrics
        metric_value = 1
        for _ in range(1, 5):
            metrics = []
            guid8 = str(uuid.uuid4())[:8]
            params = [Param(f"batch param-{guid8}-{val}", value=str(val)) for val in range(5)]
            tags = [RunTag(f"batch tag-{guid8}-{val}", value=str(val)) for val in range(5)]
            for _ in range(0, 50):
                metric_value += 1
                metrics.append(
                    Metric(
                        key=f"batch metrics async-{metric_value}",
                        value=time.time(),
                        timestamp=metric_value,
                        step=0,
                    )
                )

            params_to_log.extend(params)
            run_operation = qcflow.log_params(
                params={param.key: param.value for param in params},
                synchronous=False,
            )
            run_operations.append(run_operation)

            tags_to_log.extend(tags)
            run_operation = qcflow.set_tags(
                tags={tag.key: tag.value for tag in tags},
                synchronous=False,
            )
            run_operations.append(run_operation)

            metrics_to_log.extend(metrics)
            run_operation = qcflow.log_metrics(
                metrics={metric.key: metric.value for metric in metrics},
                step=1,
                synchronous=False,
            )
            run_operations.append(run_operation)

    for run_operation in run_operations:
        run_operation.wait()

    run = qcflow.run
    run = qcflow.get_run(run_id)
    for tag in tags_to_log:
        assert tag.key in run.data.tags
        assert tag.value == run.data.tags[tag.key]
    for param in params_to_log:
        assert param.key in run.data.params
        assert param.value == run.data.params[param.key]
    for metric in metrics_to_log:
        assert metric.key in run.data.metrics
        assert metric.value == run.data.metrics[metric.key]


def test_async_logging_fluent_check_batch_split():
    # Check that batch is split into multiple requests if it exceeds the maximum size
    # and if we wait for RunOperations returned then at the end everything should be logged.
    experiment_name = f"qcflow-async-logging-test-{str(uuid.uuid4())[:8]}"
    experiment_id = qcflow.create_experiment(experiment_name)

    run_operations = []

    with qcflow.start_run(experiment_id=experiment_id) as run:
        run_id = run.info.run_id

        metrics_to_log = {
            f"batch metrics async-{metric_value}": metric_value for metric_value in range(0, 10000)
        }

        run_operations = qcflow.log_metrics(
            metrics=metrics_to_log,
            step=1,
            synchronous=False,
        )

        run_operations.wait()

    # Total 10000 metrics logged, max batch size =1000, so 10 requests will be sent.
    assert len(run_operations._operation_futures) == 10

    run = qcflow.run
    run = qcflow.get_run(run_id)
    for metric_key, metric_value in metrics_to_log.items():
        assert metric_key in run.data.metrics
        assert metric_value == run.data.metrics[metric_key]
