"""
Integration test which starts a local Tracking Server on an ephemeral port,
and ensures we can use the tracking API to communicate with it.
"""

import json
import logging
import math
import os
import pathlib
import posixpath
import sys
import time
import urllib.parse
from unittest import mock

import flask
import pandas as pd
import pytest
import requests

import qcflow.experiments
import qcflow.pyfunc
from qcflow import MlflowClient
from qcflow.artifacts import download_artifacts
from qcflow.data.pandas_dataset import from_pandas
from qcflow.entities import (
    Dataset,
    DatasetInput,
    InputTag,
    Metric,
    Param,
    RunInputs,
    RunTag,
    ViewType,
)
from qcflow.entities.trace_data import TraceData
from qcflow.entities.trace_status import TraceStatus
from qcflow.exceptions import MlflowException, RestException
from qcflow.models import Model
from qcflow.protos.databricks_pb2 import RESOURCE_DOES_NOT_EXIST, ErrorCode
from qcflow.server.handlers import _get_sampled_steps_from_steps
from qcflow.store.tracking.sqlalchemy_store import SqlAlchemyStore
from qcflow.tracing.constant import TraceTagKey
from qcflow.utils import qcflow_tags
from qcflow.utils.file_utils import TempDir, path_to_local_file_uri
from qcflow.utils.qcflow_tags import (
    QCFLOW_DATASET_CONTEXT,
    QCFLOW_GIT_COMMIT,
    QCFLOW_PARENT_RUN_ID,
    QCFLOW_PROJECT_ENTRY_POINT,
    QCFLOW_SOURCE_NAME,
    QCFLOW_SOURCE_TYPE,
    QCFLOW_USER,
)
from qcflow.utils.os import is_windows
from qcflow.utils.proto_json_utils import message_to_json
from qcflow.utils.time import get_current_time_millis

from tests.integration.utils import invoke_cli_runner
from tests.tracking.integration_test_utils import (
    _init_server,
    _send_rest_tracking_post_request,
)

_logger = logging.getLogger(__name__)


@pytest.fixture(params=["file", "sqlalchemy"])
def qcflow_client(request, tmp_path):
    """Provides an QCFlow Tracking API client pointed at the local tracking server."""
    if request.param == "file":
        backend_uri = tmp_path.joinpath("file").as_uri()
    elif request.param == "sqlalchemy":
        path = tmp_path.joinpath("sqlalchemy.db").as_uri()
        backend_uri = ("sqlite://" if sys.platform == "win32" else "sqlite:////") + path[
            len("file://") :
        ]

    with _init_server(backend_uri, root_artifact_uri=tmp_path.as_uri()) as url:
        yield MlflowClient(url)


@pytest.fixture
def cli_env(qcflow_client):
    """Provides an environment for the QCFlow CLI pointed at the local tracking server."""
    return {
        "LC_ALL": "en_US.UTF-8",
        "LANG": "en_US.UTF-8",
        "QCFLOW_TRACKING_URI": qcflow_client.tracking_uri,
    }


def create_experiments(client, names):
    return [client.create_experiment(n) for n in names]


def test_create_get_search_experiment(qcflow_client):
    experiment_id = qcflow_client.create_experiment(
        "My Experiment", artifact_location="my_location", tags={"key1": "val1", "key2": "val2"}
    )
    exp = qcflow_client.get_experiment(experiment_id)
    assert exp.name == "My Experiment"
    if is_windows():
        assert exp.artifact_location == pathlib.Path.cwd().joinpath("my_location").as_uri()
    else:
        assert exp.artifact_location == str(pathlib.Path.cwd().joinpath("my_location"))
    assert len(exp.tags) == 2
    assert exp.tags["key1"] == "val1"
    assert exp.tags["key2"] == "val2"

    experiments = qcflow_client.search_experiments()
    assert {e.name for e in experiments} == {"My Experiment", "Default"}
    qcflow_client.delete_experiment(experiment_id)
    assert {e.name for e in qcflow_client.search_experiments()} == {"Default"}
    assert {e.name for e in qcflow_client.search_experiments(view_type=ViewType.ACTIVE_ONLY)} == {
        "Default"
    }
    assert {e.name for e in qcflow_client.search_experiments(view_type=ViewType.DELETED_ONLY)} == {
        "My Experiment"
    }
    assert {e.name for e in qcflow_client.search_experiments(view_type=ViewType.ALL)} == {
        "My Experiment",
        "Default",
    }
    active_exps_paginated = qcflow_client.search_experiments(max_results=1)
    assert {e.name for e in active_exps_paginated} == {"Default"}
    assert active_exps_paginated.token is None

    all_exps_paginated = qcflow_client.search_experiments(max_results=1, view_type=ViewType.ALL)
    first_page_names = {e.name for e in all_exps_paginated}
    all_exps_second_page = qcflow_client.search_experiments(
        max_results=1, view_type=ViewType.ALL, page_token=all_exps_paginated.token
    )
    second_page_names = {e.name for e in all_exps_second_page}
    assert len(first_page_names) == 1
    assert len(second_page_names) == 1
    assert first_page_names.union(second_page_names) == {"Default", "My Experiment"}


def test_create_experiment_validation(qcflow_client):
    def assert_bad_request(payload, expected_error_message):
        response = _send_rest_tracking_post_request(
            qcflow_client.tracking_uri,
            "/api/2.0/qcflow/experiments/create",
            payload,
        )
        assert response.status_code == 400
        assert expected_error_message in response.text

    assert_bad_request(
        {
            "name": 123,
        },
        "Invalid value 123 for parameter 'name'",
    )
    assert_bad_request({}, "Missing value for required parameter 'name'")
    assert_bad_request(
        {
            "name": "experiment name",
            "artifact_location": 9.0,
            "tags": [{"key": "key", "value": "value"}],
        },
        "Invalid value 9.0 for parameter 'artifact_location'",
    )
    assert_bad_request(
        {
            "name": "experiment name",
            "artifact_location": "my_location",
            "tags": "5",
        },
        "Invalid value \\\"5\\\" for parameter 'tags'",
    )


def test_delete_restore_experiment(qcflow_client):
    experiment_id = qcflow_client.create_experiment("Deleterious")
    assert qcflow_client.get_experiment(experiment_id).lifecycle_stage == "active"
    qcflow_client.delete_experiment(experiment_id)
    assert qcflow_client.get_experiment(experiment_id).lifecycle_stage == "deleted"
    qcflow_client.restore_experiment(experiment_id)
    assert qcflow_client.get_experiment(experiment_id).lifecycle_stage == "active"


def test_delete_restore_experiment_cli(qcflow_client, cli_env):
    experiment_name = "DeleteriousCLI"
    invoke_cli_runner(
        qcflow.experiments.commands, ["create", "--experiment-name", experiment_name], env=cli_env
    )
    experiment_id = qcflow_client.get_experiment_by_name(experiment_name).experiment_id
    assert qcflow_client.get_experiment(experiment_id).lifecycle_stage == "active"
    invoke_cli_runner(
        qcflow.experiments.commands, ["delete", "-x", str(experiment_id)], env=cli_env
    )
    assert qcflow_client.get_experiment(experiment_id).lifecycle_stage == "deleted"
    invoke_cli_runner(
        qcflow.experiments.commands, ["restore", "-x", str(experiment_id)], env=cli_env
    )
    assert qcflow_client.get_experiment(experiment_id).lifecycle_stage == "active"


def test_rename_experiment(qcflow_client):
    experiment_id = qcflow_client.create_experiment("BadName")
    assert qcflow_client.get_experiment(experiment_id).name == "BadName"
    qcflow_client.rename_experiment(experiment_id, "GoodName")
    assert qcflow_client.get_experiment(experiment_id).name == "GoodName"


def test_rename_experiment_cli(qcflow_client, cli_env):
    bad_experiment_name = "CLIBadName"
    good_experiment_name = "CLIGoodName"

    invoke_cli_runner(
        qcflow.experiments.commands, ["create", "-n", bad_experiment_name], env=cli_env
    )
    experiment_id = qcflow_client.get_experiment_by_name(bad_experiment_name).experiment_id
    assert qcflow_client.get_experiment(experiment_id).name == bad_experiment_name
    invoke_cli_runner(
        qcflow.experiments.commands,
        ["rename", "--experiment-id", str(experiment_id), "--new-name", good_experiment_name],
        env=cli_env,
    )
    assert qcflow_client.get_experiment(experiment_id).name == good_experiment_name


@pytest.mark.parametrize("parent_run_id_kwarg", [None, "my-parent-id"])
def test_create_run_all_args(qcflow_client, parent_run_id_kwarg):
    user = "username"
    source_name = "Hello"
    entry_point = "entry"
    source_version = "abc"
    create_run_kwargs = {
        "start_time": 456,
        "run_name": "my name",
        "tags": {
            QCFLOW_USER: user,
            QCFLOW_SOURCE_TYPE: "LOCAL",
            QCFLOW_SOURCE_NAME: source_name,
            QCFLOW_PROJECT_ENTRY_POINT: entry_point,
            QCFLOW_GIT_COMMIT: source_version,
            QCFLOW_PARENT_RUN_ID: "7",
            "my": "tag",
            "other": "tag",
        },
    }
    experiment_id = qcflow_client.create_experiment(
        f"Run A Lot (parent_run_id={parent_run_id_kwarg})"
    )
    created_run = qcflow_client.create_run(experiment_id, **create_run_kwargs)
    run_id = created_run.info.run_id
    _logger.info(f"Run id={run_id}")
    fetched_run = qcflow_client.get_run(run_id)
    for run in [created_run, fetched_run]:
        assert run.info.run_id == run_id
        assert run.info.run_uuid == run_id
        assert run.info.experiment_id == experiment_id
        assert run.info.user_id == user
        assert run.info.start_time == create_run_kwargs["start_time"]
        assert run.info.run_name == "my name"
        for tag in create_run_kwargs["tags"]:
            assert tag in run.data.tags
        assert run.data.tags.get(QCFLOW_USER) == user
        assert run.data.tags.get(QCFLOW_PARENT_RUN_ID) == parent_run_id_kwarg or "7"
        assert [run.info for run in qcflow_client.search_runs([experiment_id])] == [run.info]


def test_create_run_defaults(qcflow_client):
    experiment_id = qcflow_client.create_experiment("Run A Little")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id
    run = qcflow_client.get_run(run_id)
    assert run.info.run_id == run_id
    assert run.info.experiment_id == experiment_id
    assert run.info.user_id == "unknown"


def test_log_metrics_params_tags(qcflow_client):
    experiment_id = qcflow_client.create_experiment("Oh My")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id
    qcflow_client.log_metric(run_id, key="metric", value=123.456, timestamp=789, step=2)
    qcflow_client.log_metric(run_id, key="nan_metric", value=float("nan"))
    qcflow_client.log_metric(run_id, key="inf_metric", value=float("inf"))
    qcflow_client.log_metric(run_id, key="-inf_metric", value=-float("inf"))
    qcflow_client.log_metric(run_id, key="stepless-metric", value=987.654, timestamp=321)
    qcflow_client.log_param(run_id, "param", "value")
    qcflow_client.set_tag(run_id, "taggity", "do-dah")
    run = qcflow_client.get_run(run_id)
    assert run.data.metrics.get("metric") == 123.456
    assert math.isnan(run.data.metrics.get("nan_metric"))
    assert run.data.metrics.get("inf_metric") >= 1.7976931348623157e308
    assert run.data.metrics.get("-inf_metric") <= -1.7976931348623157e308
    assert run.data.metrics.get("stepless-metric") == 987.654
    assert run.data.params.get("param") == "value"
    assert run.data.tags.get("taggity") == "do-dah"
    metric_history0 = qcflow_client.get_metric_history(run_id, "metric")
    assert len(metric_history0) == 1
    metric0 = metric_history0[0]
    assert metric0.key == "metric"
    assert metric0.value == 123.456
    assert metric0.timestamp == 789
    assert metric0.step == 2
    metric_history1 = qcflow_client.get_metric_history(run_id, "stepless-metric")
    assert len(metric_history1) == 1
    metric1 = metric_history1[0]
    assert metric1.key == "stepless-metric"
    assert metric1.value == 987.654
    assert metric1.timestamp == 321
    assert metric1.step == 0

    metric_history = qcflow_client.get_metric_history(run_id, "a_test_accuracy")
    assert metric_history == []


def test_log_metric_validation(qcflow_client):
    experiment_id = qcflow_client.create_experiment("metrics validation")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id

    def assert_bad_request(payload, expected_error_message):
        response = _send_rest_tracking_post_request(
            qcflow_client.tracking_uri,
            "/api/2.0/qcflow/runs/log-metric",
            payload,
        )
        assert response.status_code == 400
        assert expected_error_message in response.text

    assert_bad_request(
        {
            "run_id": 31,
            "key": "metric",
            "value": 41,
            "timestamp": 59,
            "step": 26,
        },
        "Invalid value 31 for parameter 'run_id' supplied",
    )
    assert_bad_request(
        {
            "run_id": run_id,
            "key": 31,
            "value": 41,
            "timestamp": 59,
            "step": 26,
        },
        "Invalid value 31 for parameter 'key' supplied",
    )
    assert_bad_request(
        {
            "run_id": run_id,
            "key": "foo",
            "value": 31,
            "timestamp": 59,
            "step": "foo",
        },
        "Invalid value \\\"foo\\\" for parameter 'step' supplied",
    )
    assert_bad_request(
        {
            "run_id": run_id,
            "key": "foo",
            "value": 31,
            "timestamp": "foo",
            "step": 41,
        },
        "Invalid value \\\"foo\\\" for parameter 'timestamp' supplied",
    )
    assert_bad_request(
        {
            "run_id": None,
            "key": "foo",
            "value": 31,
            "timestamp": 59,
            "step": 41,
        },
        "Missing value for required parameter 'run_id'",
    )
    assert_bad_request(
        {
            "run_id": run_id,
            # Missing key
            "value": 31,
            "timestamp": 59,
            "step": 41,
        },
        "Missing value for required parameter 'key'",
    )
    assert_bad_request(
        {
            "run_id": run_id,
            "key": None,
            "value": 31,
            "timestamp": 59,
            "step": 41,
        },
        "Missing value for required parameter 'key'",
    )


def test_log_param_validation(qcflow_client):
    experiment_id = qcflow_client.create_experiment("params validation")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id

    def assert_bad_request(payload, expected_error_message):
        response = _send_rest_tracking_post_request(
            qcflow_client.tracking_uri,
            "/api/2.0/qcflow/runs/log-parameter",
            payload,
        )
        assert response.status_code == 400
        assert expected_error_message in response.text

    assert_bad_request(
        {
            "run_id": 31,
            "key": "param",
            "value": 41,
        },
        "Invalid value 31 for parameter 'run_id' supplied",
    )
    assert_bad_request(
        {
            "run_id": run_id,
            "key": 31,
            "value": 41,
        },
        "Invalid value 31 for parameter 'key' supplied",
    )


def test_log_param_with_empty_string_as_value(qcflow_client):
    experiment_id = qcflow_client.create_experiment(
        test_log_param_with_empty_string_as_value.__name__
    )
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id

    qcflow_client.log_param(run_id, "param_key", "")
    assert {"param_key": ""}.items() <= qcflow_client.get_run(run_id).data.params.items()


def test_set_tag_with_empty_string_as_value(qcflow_client):
    experiment_id = qcflow_client.create_experiment(
        test_set_tag_with_empty_string_as_value.__name__
    )
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id

    qcflow_client.set_tag(run_id, "tag_key", "")
    assert {"tag_key": ""}.items() <= qcflow_client.get_run(run_id).data.tags.items()


def test_log_batch_containing_params_and_tags_with_empty_string_values(qcflow_client):
    experiment_id = qcflow_client.create_experiment(
        test_log_batch_containing_params_and_tags_with_empty_string_values.__name__
    )
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id

    qcflow_client.log_batch(
        run_id=run_id,
        params=[Param("param_key", "")],
        tags=[RunTag("tag_key", "")],
    )
    assert {"param_key": ""}.items() <= qcflow_client.get_run(run_id).data.params.items()
    assert {"tag_key": ""}.items() <= qcflow_client.get_run(run_id).data.tags.items()


def test_set_tag_validation(qcflow_client):
    experiment_id = qcflow_client.create_experiment("tags validation")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id

    def assert_bad_request(payload, expected_error_message):
        response = _send_rest_tracking_post_request(
            qcflow_client.tracking_uri,
            "/api/2.0/qcflow/runs/set-tag",
            payload,
        )
        assert response.status_code == 400
        assert expected_error_message in response.text

    assert_bad_request(
        {
            "run_id": 31,
            "key": "tag",
            "value": 41,
        },
        "Invalid value 31 for parameter 'run_id' supplied",
    )
    assert_bad_request(
        {
            "run_id": run_id,
            "key": "param",
            "value": 41,
        },
        "Invalid value 41 for parameter 'value' supplied",
    )
    assert_bad_request(
        {
            "run_id": run_id,
            # Missing key
            "value": "value",
        },
        "Missing value for required parameter 'key'",
    )

    response = _send_rest_tracking_post_request(
        qcflow_client.tracking_uri,
        "/api/2.0/qcflow/runs/set-tag",
        {
            "run_uuid": run_id,
            "key": "key",
            "value": "value",
        },
    )
    assert response.status_code == 200


def test_path_validation(qcflow_client):
    experiment_id = qcflow_client.create_experiment("tags validation")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id
    invalid_path = "../path"

    def assert_response(resp):
        assert resp.status_code == 400
        assert response.json() == {
            "error_code": "INVALID_PARAMETER_VALUE",
            "message": "Invalid path",
        }

    response = requests.get(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/artifacts/list",
        params={"run_id": run_id, "path": invalid_path},
    )
    assert_response(response)

    response = requests.get(
        f"{qcflow_client.tracking_uri}/get-artifact",
        params={"run_id": run_id, "path": invalid_path},
    )
    assert_response(response)

    response = requests.get(
        f"{qcflow_client.tracking_uri}//model-versions/get-artifact",
        params={"name": "model", "version": 1, "path": invalid_path},
    )
    assert_response(response)


def test_set_experiment_tag(qcflow_client):
    experiment_id = qcflow_client.create_experiment("SetExperimentTagTest")
    qcflow_client.set_experiment_tag(experiment_id, "dataset", "imagenet1K")
    experiment = qcflow_client.get_experiment(experiment_id)
    assert "dataset" in experiment.tags
    assert experiment.tags["dataset"] == "imagenet1K"
    # test that updating a tag works
    qcflow_client.set_experiment_tag(experiment_id, "dataset", "birdbike")
    experiment = qcflow_client.get_experiment(experiment_id)
    assert "dataset" in experiment.tags
    assert experiment.tags["dataset"] == "birdbike"
    # test that setting a tag on 1 experiment does not impact another experiment.
    experiment_id_2 = qcflow_client.create_experiment("SetExperimentTagTest2")
    experiment2 = qcflow_client.get_experiment(experiment_id_2)
    assert len(experiment2.tags) == 0
    # test that setting a tag on different experiments maintain different values across experiments
    qcflow_client.set_experiment_tag(experiment_id_2, "dataset", "birds200")
    experiment = qcflow_client.get_experiment(experiment_id)
    experiment2 = qcflow_client.get_experiment(experiment_id_2)
    assert "dataset" in experiment.tags
    assert experiment.tags["dataset"] == "birdbike"
    assert "dataset" in experiment2.tags
    assert experiment2.tags["dataset"] == "birds200"
    # test can set multi-line tags
    qcflow_client.set_experiment_tag(experiment_id, "multiline tag", "value2\nvalue2\nvalue2")
    experiment = qcflow_client.get_experiment(experiment_id)
    assert "multiline tag" in experiment.tags
    assert experiment.tags["multiline tag"] == "value2\nvalue2\nvalue2"


def test_set_experiment_tag_with_empty_string_as_value(qcflow_client):
    experiment_id = qcflow_client.create_experiment(
        test_set_experiment_tag_with_empty_string_as_value.__name__
    )
    qcflow_client.set_experiment_tag(experiment_id, "tag_key", "")
    assert {"tag_key": ""}.items() <= qcflow_client.get_experiment(experiment_id).tags.items()


def test_delete_tag(qcflow_client):
    experiment_id = qcflow_client.create_experiment("DeleteTagExperiment")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id
    qcflow_client.log_metric(run_id, key="metric", value=123.456, timestamp=789, step=2)
    qcflow_client.log_metric(run_id, key="stepless-metric", value=987.654, timestamp=321)
    qcflow_client.log_param(run_id, "param", "value")
    qcflow_client.set_tag(run_id, "taggity", "do-dah")
    run = qcflow_client.get_run(run_id)
    assert "taggity" in run.data.tags
    assert run.data.tags["taggity"] == "do-dah"
    qcflow_client.delete_tag(run_id, "taggity")
    run = qcflow_client.get_run(run_id)
    assert "taggity" not in run.data.tags
    with pytest.raises(MlflowException, match=r"Run .+ not found"):
        qcflow_client.delete_tag("fake_run_id", "taggity")
    with pytest.raises(MlflowException, match="No tag with name: fakeTag"):
        qcflow_client.delete_tag(run_id, "fakeTag")
    qcflow_client.delete_run(run_id)
    with pytest.raises(MlflowException, match=f"The run {run_id} must be in"):
        qcflow_client.delete_tag(run_id, "taggity")


def test_log_batch(qcflow_client):
    experiment_id = qcflow_client.create_experiment("Batch em up")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id
    qcflow_client.log_batch(
        run_id=run_id,
        metrics=[Metric("metric", 123.456, 789, 3)],
        params=[Param("param", "value")],
        tags=[RunTag("taggity", "do-dah")],
    )
    run = qcflow_client.get_run(run_id)
    assert run.data.metrics.get("metric") == 123.456
    assert run.data.params.get("param") == "value"
    assert run.data.tags.get("taggity") == "do-dah"
    metric_history = qcflow_client.get_metric_history(run_id, "metric")
    assert len(metric_history) == 1
    metric = metric_history[0]
    assert metric.key == "metric"
    assert metric.value == 123.456
    assert metric.timestamp == 789
    assert metric.step == 3


def test_log_batch_validation(qcflow_client):
    experiment_id = qcflow_client.create_experiment("log_batch validation")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id

    def assert_bad_request(payload, expected_error_message):
        response = _send_rest_tracking_post_request(
            qcflow_client.tracking_uri,
            "/api/2.0/qcflow/runs/log-batch",
            payload,
        )
        assert response.status_code == 400
        assert expected_error_message in response.text

    for request_parameter in ["metrics", "params", "tags"]:
        assert_bad_request(
            {
                "run_id": run_id,
                request_parameter: "foo",
            },
            f"Invalid value \\\"foo\\\" for parameter '{request_parameter}' supplied",
        )

    ## Should 400 if missing timestamp
    assert_bad_request(
        {"run_id": run_id, "metrics": [{"key": "mae", "value": 2.5}]},
        "Missing value for required parameter 'metrics[0].timestamp'",
    )

    ## Should 200 if timestamp provided but step is not
    response = _send_rest_tracking_post_request(
        qcflow_client.tracking_uri,
        "/api/2.0/qcflow/runs/log-batch",
        {"run_id": run_id, "metrics": [{"key": "mae", "value": 2.5, "timestamp": 123456789}]},
    )

    assert response.status_code == 200


@pytest.mark.allow_infer_pip_requirements_fallback
def test_log_model(qcflow_client):
    experiment_id = qcflow_client.create_experiment("Log models")
    with TempDir(chdr=True):
        model_paths = [f"model/path/{i}" for i in range(3)]
        qcflow.set_tracking_uri(qcflow_client.tracking_uri)
        with qcflow.start_run(experiment_id=experiment_id) as run:
            for i, m in enumerate(model_paths):
                qcflow.pyfunc.log_model(m, loader_module="qcflow.pyfunc")
                qcflow.pyfunc.save_model(
                    m,
                    qcflow_model=Model(artifact_path=m, run_id=run.info.run_id),
                    loader_module="qcflow.pyfunc",
                )
                model = Model.load(os.path.join(m, "MLmodel"))
                run = qcflow.get_run(run.info.run_id)
                tag = run.data.tags["qcflow.log-model.history"]
                models = json.loads(tag)
                model.utc_time_created = models[i]["utc_time_created"]

                history_model_meta = models[i].copy()
                original_model_uuid = history_model_meta.pop("model_uuid")
                model_meta = model.get_tags_dict().copy()
                new_model_uuid = model_meta.pop("model_uuid")
                assert history_model_meta == model_meta
                assert original_model_uuid != new_model_uuid
                assert len(models) == i + 1
                for j in range(0, i + 1):
                    assert models[j]["artifact_path"] == model_paths[j]


def test_set_terminated_defaults(qcflow_client):
    experiment_id = qcflow_client.create_experiment("Terminator 1")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id
    assert qcflow_client.get_run(run_id).info.status == "RUNNING"
    assert qcflow_client.get_run(run_id).info.end_time is None
    qcflow_client.set_terminated(run_id)
    assert qcflow_client.get_run(run_id).info.status == "FINISHED"
    assert qcflow_client.get_run(run_id).info.end_time <= get_current_time_millis()


def test_set_terminated_status(qcflow_client):
    experiment_id = qcflow_client.create_experiment("Terminator 2")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id
    assert qcflow_client.get_run(run_id).info.status == "RUNNING"
    assert qcflow_client.get_run(run_id).info.end_time is None
    qcflow_client.set_terminated(run_id, "FAILED")
    assert qcflow_client.get_run(run_id).info.status == "FAILED"
    assert qcflow_client.get_run(run_id).info.end_time <= get_current_time_millis()


def test_artifacts(qcflow_client, tmp_path):
    experiment_id = qcflow_client.create_experiment("Art In Fact")
    experiment_info = qcflow_client.get_experiment(experiment_id)
    assert experiment_info.artifact_location.startswith(path_to_local_file_uri(str(tmp_path)))
    artifact_path = urllib.parse.urlparse(experiment_info.artifact_location).path
    assert posixpath.split(artifact_path)[-1] == experiment_id

    created_run = qcflow_client.create_run(experiment_id)
    assert created_run.info.artifact_uri.startswith(experiment_info.artifact_location)
    run_id = created_run.info.run_id
    src_dir = tmp_path.joinpath("test_artifacts_src")
    src_dir.mkdir()
    src_file = os.path.join(src_dir, "my.file")
    with open(src_file, "w") as f:
        f.write("Hello, World!")
    qcflow_client.log_artifact(run_id, src_file, None)
    qcflow_client.log_artifacts(run_id, src_dir, "dir")

    root_artifacts_list = qcflow_client.list_artifacts(run_id)
    assert {a.path for a in root_artifacts_list} == {"my.file", "dir"}

    dir_artifacts_list = qcflow_client.list_artifacts(run_id, "dir")
    assert {a.path for a in dir_artifacts_list} == {"dir/my.file"}

    all_artifacts = download_artifacts(
        run_id=run_id, artifact_path=".", tracking_uri=qcflow_client.tracking_uri
    )
    with open(f"{all_artifacts}/my.file") as f:
        assert f.read() == "Hello, World!"
    with open(f"{all_artifacts}/dir/my.file") as f:
        assert f.read() == "Hello, World!"

    dir_artifacts = download_artifacts(
        run_id=run_id, artifact_path="dir", tracking_uri=qcflow_client.tracking_uri
    )
    with open(f"{dir_artifacts}/my.file") as f:
        assert f.read() == "Hello, World!"


def test_search_pagination(qcflow_client):
    experiment_id = qcflow_client.create_experiment("search_pagination")
    runs = [qcflow_client.create_run(experiment_id, start_time=1).info.run_id for _ in range(0, 10)]
    runs = sorted(runs)
    result = qcflow_client.search_runs([experiment_id], max_results=4, page_token=None)
    assert [r.info.run_id for r in result] == runs[0:4]
    assert result.token is not None
    result = qcflow_client.search_runs([experiment_id], max_results=4, page_token=result.token)
    assert [r.info.run_id for r in result] == runs[4:8]
    assert result.token is not None
    result = qcflow_client.search_runs([experiment_id], max_results=4, page_token=result.token)
    assert [r.info.run_id for r in result] == runs[8:]
    assert result.token is None


def test_search_validation(qcflow_client):
    experiment_id = qcflow_client.create_experiment("search_validation")
    with pytest.raises(
        MlflowException, match=r"Invalid value 123456789 for parameter 'max_results' supplied"
    ):
        qcflow_client.search_runs([experiment_id], max_results=123456789)


def test_get_experiment_by_name(qcflow_client):
    name = "test_get_experiment_by_name"
    experiment_id = qcflow_client.create_experiment(name)
    res = qcflow_client.get_experiment_by_name(name)
    assert res.experiment_id == experiment_id
    assert res.name == name
    assert qcflow_client.get_experiment_by_name("idontexist") is None


def test_get_experiment(qcflow_client):
    name = "test_get_experiment"
    experiment_id = qcflow_client.create_experiment(name)
    res = qcflow_client.get_experiment(experiment_id)
    assert res.experiment_id == experiment_id
    assert res.name == name


def test_search_experiments(qcflow_client):
    # To ensure the default experiment and non-default experiments have different creation_time
    # for deterministic search results, send a request to the server and initialize the tracking
    # store.
    assert qcflow_client.search_experiments()[0].name == "Default"

    experiments = [
        ("a", {"key": "value"}),
        ("ab", {"key": "vaLue"}),
        ("Abc", None),
    ]
    experiment_ids = []
    for name, tags in experiments:
        # sleep for windows file system current_time precision in Python to enforce
        # deterministic ordering based on last_update_time (creation_time due to no
        # mutation of experiment state)
        time.sleep(0.001)
        experiment_ids.append(qcflow_client.create_experiment(name, tags=tags))

    # filter_string
    experiments = qcflow_client.search_experiments(filter_string="attribute.name = 'a'")
    assert [e.name for e in experiments] == ["a"]
    experiments = qcflow_client.search_experiments(filter_string="attribute.name != 'a'")
    assert [e.name for e in experiments] == ["Abc", "ab", "Default"]
    experiments = qcflow_client.search_experiments(filter_string="name LIKE 'a%'")
    assert [e.name for e in experiments] == ["ab", "a"]
    experiments = qcflow_client.search_experiments(filter_string="tag.key = 'value'")
    assert [e.name for e in experiments] == ["a"]
    experiments = qcflow_client.search_experiments(filter_string="tag.key != 'value'")
    assert [e.name for e in experiments] == ["ab"]
    experiments = qcflow_client.search_experiments(filter_string="tag.key ILIKE '%alu%'")
    assert [e.name for e in experiments] == ["ab", "a"]

    # order_by
    experiments = qcflow_client.search_experiments(order_by=["name DESC"])
    assert [e.name for e in experiments] == ["ab", "a", "Default", "Abc"]

    # max_results
    experiments = qcflow_client.search_experiments(max_results=2)
    assert [e.name for e in experiments] == ["Abc", "ab"]
    # page_token
    experiments = qcflow_client.search_experiments(page_token=experiments.token)
    assert [e.name for e in experiments] == ["a", "Default"]

    # view_type
    time.sleep(0.001)
    qcflow_client.delete_experiment(experiment_ids[1])
    experiments = qcflow_client.search_experiments(view_type=ViewType.ACTIVE_ONLY)
    assert [e.name for e in experiments] == ["Abc", "a", "Default"]
    experiments = qcflow_client.search_experiments(view_type=ViewType.DELETED_ONLY)
    assert [e.name for e in experiments] == ["ab"]
    experiments = qcflow_client.search_experiments(view_type=ViewType.ALL)
    assert [e.name for e in experiments] == ["Abc", "ab", "a", "Default"]


def test_get_metric_history_bulk_rejects_invalid_requests(qcflow_client):
    def assert_response(resp, message_part):
        assert resp.status_code == 400
        response_json = resp.json()
        assert response_json.get("error_code") == "INVALID_PARAMETER_VALUE"
        assert message_part in response_json.get("message", "")

    response_no_run_ids_field = requests.get(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/metrics/get-history-bulk",
        params={"metric_key": "key"},
    )
    assert_response(
        response_no_run_ids_field,
        "GetMetricHistoryBulk request must specify at least one run_id",
    )

    response_empty_run_ids = requests.get(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/metrics/get-history-bulk",
        params={"run_id": [], "metric_key": "key"},
    )
    assert_response(
        response_empty_run_ids,
        "GetMetricHistoryBulk request must specify at least one run_id",
    )

    response_too_many_run_ids = requests.get(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/metrics/get-history-bulk",
        params={"run_id": [f"id_{i}" for i in range(1000)], "metric_key": "key"},
    )
    assert_response(
        response_too_many_run_ids,
        "GetMetricHistoryBulk request cannot specify more than",
    )

    response_no_metric_key_field = requests.get(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/metrics/get-history-bulk",
        params={"run_id": ["123"]},
    )
    assert_response(
        response_no_metric_key_field,
        "GetMetricHistoryBulk request must specify a metric_key",
    )


def test_get_metric_history_bulk_returns_expected_metrics_in_expected_order(qcflow_client):
    experiment_id = qcflow_client.create_experiment("get metric history bulk")
    created_run1 = qcflow_client.create_run(experiment_id)
    run_id1 = created_run1.info.run_id
    created_run2 = qcflow_client.create_run(experiment_id)
    run_id2 = created_run2.info.run_id
    created_run3 = qcflow_client.create_run(experiment_id)
    run_id3 = created_run3.info.run_id

    metricA_history = [
        {"key": "metricA", "timestamp": 1, "step": 2, "value": 10.0},
        {"key": "metricA", "timestamp": 1, "step": 3, "value": 11.0},
        {"key": "metricA", "timestamp": 1, "step": 3, "value": 12.0},
        {"key": "metricA", "timestamp": 2, "step": 3, "value": 12.0},
    ]
    for metric in metricA_history:
        qcflow_client.log_metric(run_id1, **metric)
        metric_for_run2 = dict(metric)
        metric_for_run2["value"] += 1.0
        qcflow_client.log_metric(run_id2, **metric_for_run2)

    metricB_history = [
        {"key": "metricB", "timestamp": 7, "step": -2, "value": -100.0},
        {"key": "metricB", "timestamp": 8, "step": 0, "value": 0.0},
        {"key": "metricB", "timestamp": 8, "step": 0, "value": 1.0},
        {"key": "metricB", "timestamp": 9, "step": 1, "value": 12.0},
    ]
    for metric in metricB_history:
        qcflow_client.log_metric(run_id1, **metric)
        metric_for_run2 = dict(metric)
        metric_for_run2["value"] += 1.0
        qcflow_client.log_metric(run_id2, **metric_for_run2)

    response_run1_metricA = requests.get(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/metrics/get-history-bulk",
        params={"run_id": [run_id1], "metric_key": "metricA"},
    )
    assert response_run1_metricA.status_code == 200
    assert response_run1_metricA.json().get("metrics") == [
        {**metric, "run_id": run_id1} for metric in metricA_history
    ]

    response_run2_metricB = requests.get(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/metrics/get-history-bulk",
        params={"run_id": [run_id2], "metric_key": "metricB"},
    )
    assert response_run2_metricB.status_code == 200
    assert response_run2_metricB.json().get("metrics") == [
        {**metric, "run_id": run_id2, "value": metric["value"] + 1.0} for metric in metricB_history
    ]

    response_run1_run2_metricA = requests.get(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/metrics/get-history-bulk",
        params={"run_id": [run_id1, run_id2], "metric_key": "metricA"},
    )
    assert response_run1_run2_metricA.status_code == 200
    assert response_run1_run2_metricA.json().get("metrics") == sorted(
        [{**metric, "run_id": run_id1} for metric in metricA_history]
        + [
            {**metric, "run_id": run_id2, "value": metric["value"] + 1.0}
            for metric in metricA_history
        ],
        key=lambda metric: metric["run_id"],
    )

    response_run1_run2_run_3_metricB = requests.get(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/metrics/get-history-bulk",
        params={"run_id": [run_id1, run_id2, run_id3], "metric_key": "metricB"},
    )
    assert response_run1_run2_run_3_metricB.status_code == 200
    assert response_run1_run2_run_3_metricB.json().get("metrics") == sorted(
        [{**metric, "run_id": run_id1} for metric in metricB_history]
        + [
            {**metric, "run_id": run_id2, "value": metric["value"] + 1.0}
            for metric in metricB_history
        ],
        key=lambda metric: metric["run_id"],
    )


def test_get_metric_history_bulk_respects_max_results(qcflow_client):
    experiment_id = qcflow_client.create_experiment("get metric history bulk")
    run_id = qcflow_client.create_run(experiment_id).info.run_id
    max_results = 2

    metricA_history = [
        {"key": "metricA", "timestamp": 1, "step": 2, "value": 10.0},
        {"key": "metricA", "timestamp": 1, "step": 3, "value": 11.0},
        {"key": "metricA", "timestamp": 1, "step": 3, "value": 12.0},
        {"key": "metricA", "timestamp": 2, "step": 3, "value": 12.0},
    ]
    for metric in metricA_history:
        qcflow_client.log_metric(run_id, **metric)

    response_limited = requests.get(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/metrics/get-history-bulk",
        params={"run_id": [run_id], "metric_key": "metricA", "max_results": max_results},
    )
    assert response_limited.status_code == 200
    assert response_limited.json().get("metrics") == [
        {**metric, "run_id": run_id} for metric in metricA_history[:max_results]
    ]


def test_get_metric_history_bulk_calls_optimized_impl_when_expected(tmp_path):
    from qcflow.server.handlers import get_metric_history_bulk_handler

    path = path_to_local_file_uri(str(tmp_path.joinpath("sqlalchemy.db")))
    uri = ("sqlite://" if sys.platform == "win32" else "sqlite:////") + path[len("file://") :]
    mock_store = mock.Mock(wraps=SqlAlchemyStore(uri, str(tmp_path)))

    flask_app = flask.Flask("test_flask_app")

    class MockRequestArgs:
        def __init__(self, args_dict):
            self.args_dict = args_dict

        def to_dict(
            self,
            flat,
        ):
            return self.args_dict

        def get(self, key, default=None):
            return self.args_dict.get(key, default)

    with (
        mock.patch("qcflow.server.handlers._get_tracking_store", return_value=mock_store),
        flask_app.test_request_context() as mock_context,
    ):
        run_ids = [str(i) for i in range(10)]
        mock_context.request.args = MockRequestArgs(
            {
                "run_id": run_ids,
                "metric_key": "mock_key",
            }
        )

        get_metric_history_bulk_handler()

        mock_store.get_metric_history_bulk.assert_called_once_with(
            run_ids=run_ids,
            metric_key="mock_key",
            max_results=25000,
        )


def test_get_metric_history_bulk_interval_rejects_invalid_requests(qcflow_client):
    def assert_response(resp, message_part):
        assert resp.status_code == 400
        response_json = resp.json()
        assert response_json.get("error_code") == "INVALID_PARAMETER_VALUE"
        assert message_part in response_json.get("message", "")

    url = f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/metrics/get-history-bulk-interval"

    assert_response(
        requests.get(url, params={"metric_key": "key"}),
        "Missing value for required parameter 'run_ids'.",
    )

    assert_response(
        requests.get(url, params={"run_ids": [], "metric_key": "key"}),
        "Missing value for required parameter 'run_ids'.",
    )

    assert_response(
        requests.get(
            url, params={"run_ids": [f"id_{i}" for i in range(1000)], "metric_key": "key"}
        ),
        "GetMetricHistoryBulkInterval request must specify at most 100 run_ids.",
    )

    assert_response(
        requests.get(url, params={"run_ids": ["123"], "metric_key": "key", "max_results": 0}),
        "max_results must be between 1 and 2500",
    )

    assert_response(
        requests.get(url, params={"run_ids": ["123"], "metric_key": ""}),
        "Missing value for required parameter 'metric_key'",
    )

    assert_response(
        requests.get(url, params={"run_ids": ["123"], "max_results": 5}),
        "Missing value for required parameter 'metric_key'",
    )

    assert_response(
        requests.get(
            url,
            params={
                "run_ids": ["123"],
                "metric_key": "key",
                "start_step": 1,
                "end_step": 0,
                "max_results": 5,
            },
        ),
        "end_step must be greater than start_step. ",
    )

    assert_response(
        requests.get(
            url, params={"run_ids": ["123"], "metric_key": "key", "start_step": 1, "max_results": 5}
        ),
        "If either start step or end step are specified, both must be specified.",
    )


def test_get_metric_history_bulk_interval_respects_max_results(qcflow_client):
    experiment_id = qcflow_client.create_experiment("get metric history bulk")
    run_id1 = qcflow_client.create_run(experiment_id).info.run_id
    metric_history = [
        {"key": "metricA", "timestamp": 1, "step": i, "value": 10.0} for i in range(10)
    ]
    for metric in metric_history:
        qcflow_client.log_metric(run_id1, **metric)

    url = f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/metrics/get-history-bulk-interval"
    response_limited = requests.get(
        url,
        params={"run_ids": [run_id1], "metric_key": "metricA", "max_results": 5},
    )
    assert response_limited.status_code == 200
    expected_steps = [0, 2, 4, 6, 8, 9]
    expected_metrics = [
        {**metric, "run_id": run_id1}
        for metric in metric_history
        if metric["step"] in expected_steps
    ]
    assert response_limited.json().get("metrics") == expected_metrics

    # with start_step and end_step
    response_limited = requests.get(
        url,
        params={
            "run_ids": [run_id1],
            "metric_key": "metricA",
            "start_step": 0,
            "end_step": 4,
            "max_results": 5,
        },
    )
    assert response_limited.status_code == 200
    assert response_limited.json().get("metrics") == [
        {**metric, "run_id": run_id1} for metric in metric_history[:5]
    ]

    # multiple runs
    run_id2 = qcflow_client.create_run(experiment_id).info.run_id
    metric_history2 = [
        {"key": "metricA", "timestamp": 1, "step": i, "value": 10.0} for i in range(20)
    ]
    for metric in metric_history2:
        qcflow_client.log_metric(run_id2, **metric)
    response_limited = requests.get(
        url,
        params={"run_ids": [run_id1, run_id2], "metric_key": "metricA", "max_results": 5},
    )
    expected_steps = [0, 4, 8, 9, 12, 16, 19]
    expected_metrics = []
    for run_id, metric_history in [(run_id1, metric_history), (run_id2, metric_history2)]:
        expected_metrics.extend(
            [
                {**metric, "run_id": run_id}
                for metric in metric_history
                if metric["step"] in expected_steps
            ]
        )
    assert response_limited.json().get("metrics") == expected_metrics

    # test metrics with same steps
    metric_history_timestamp2 = [
        {"key": "metricA", "timestamp": 2, "step": i, "value": 10.0} for i in range(10)
    ]
    for metric in metric_history_timestamp2:
        qcflow_client.log_metric(run_id1, **metric)

    response_limited = requests.get(
        url,
        params={"run_ids": [run_id1], "metric_key": "metricA", "max_results": 5},
    )
    assert response_limited.status_code == 200
    expected_steps = [0, 2, 4, 6, 8, 9]
    expected_metrics = [
        {"key": "metricA", "timestamp": j, "step": i, "value": 10.0, "run_id": run_id1}
        for i in expected_steps
        for j in [1, 2]
    ]
    assert response_limited.json().get("metrics") == expected_metrics


@pytest.mark.parametrize(
    ("min_step", "max_step", "max_results", "nums", "expected"),
    [
        # should be evenly spaced and include the beginning and
        # end despite sometimes making it go above max_results
        (0, 10, 5, list(range(10)), {0, 2, 4, 6, 8, 9}),
        # if the clipped list is shorter than max_results,
        # then everything will be returned
        (4, 8, 5, list(range(10)), {4, 5, 6, 7, 8}),
        # works if steps are logged in intervals
        (0, 100, 5, list(range(0, 101, 20)), {0, 20, 40, 60, 80, 100}),
        (0, 1000, 5, list(range(0, 1001, 10)), {0, 200, 400, 600, 800, 1000}),
    ],
)
def test_get_sampled_steps_from_steps(min_step, max_step, max_results, nums, expected):
    assert _get_sampled_steps_from_steps(min_step, max_step, max_results, nums) == expected


def test_search_dataset_handler_rejects_invalid_requests(qcflow_client):
    def assert_response(resp, message_part):
        assert resp.status_code == 400
        response_json = resp.json()
        assert response_json.get("error_code") == "INVALID_PARAMETER_VALUE"
        assert message_part in response_json.get("message", "")

    response_no_experiment_id_field = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/experiments/search-datasets",
        json={},
    )
    assert_response(
        response_no_experiment_id_field,
        "SearchDatasets request must specify at least one experiment_id.",
    )

    response_empty_experiment_id_field = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/experiments/search-datasets",
        json={"experiment_ids": []},
    )
    assert_response(
        response_empty_experiment_id_field,
        "SearchDatasets request must specify at least one experiment_id.",
    )

    response_too_many_experiment_ids = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/experiments/search-datasets",
        json={"experiment_ids": [f"id_{i}" for i in range(1000)]},
    )
    assert_response(
        response_too_many_experiment_ids,
        "SearchDatasets request cannot specify more than",
    )


def test_search_dataset_handler_returns_expected_results(qcflow_client):
    experiment_id = qcflow_client.create_experiment("log inputs test")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id

    dataset1 = Dataset(
        name="name1",
        digest="digest1",
        source_type="source_type1",
        source="source1",
    )
    dataset_inputs1 = [
        DatasetInput(
            dataset=dataset1, tags=[InputTag(key=QCFLOW_DATASET_CONTEXT, value="training")]
        )
    ]
    qcflow_client.log_inputs(run_id, dataset_inputs1)

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/experiments/search-datasets",
        json={"experiment_ids": [experiment_id]},
    )
    expected = {
        "experiment_id": experiment_id,
        "name": "name1",
        "digest": "digest1",
        "context": "training",
    }

    assert response.status_code == 200
    assert response.json().get("dataset_summaries") == [expected]


def test_create_model_version_with_path_source(qcflow_client):
    name = "model"
    qcflow_client.create_registered_model(name)
    exp_id = qcflow_client.create_experiment("test")
    run = qcflow_client.create_run(experiment_id=exp_id)

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": run.info.artifact_uri[len("file://") :],
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 200

    # run_id is not specified
    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": run.info.artifact_uri[len("file://") :],
        },
    )
    assert response.status_code == 400
    assert "To use a local path as a model version" in response.json()["message"]

    # run_id is specified but source is not in the run's artifact directory
    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "/tmp",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 400
    assert "To use a local path as a model version" in response.json()["message"]


def test_create_model_version_with_non_local_source(qcflow_client):
    name = "model"
    qcflow_client.create_registered_model(name)
    exp_id = qcflow_client.create_experiment("test")
    run = qcflow_client.create_run(experiment_id=exp_id)

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": run.info.artifact_uri[len("file://") :],
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 200

    # Test that remote uri's supplied as a source with absolute paths work fine
    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "qcflow-artifacts:/models",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 200

    # A single trailing slash
    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "qcflow-artifacts:/models/",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 200

    # Multiple trailing slashes
    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "qcflow-artifacts:/models///",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 200

    # Multiple slashes
    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "qcflow-artifacts:/models/foo///bar",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 200

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "qcflow-artifacts://host:9000/models",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 200

    # Multiple dots
    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "qcflow-artifacts://host:9000/models/artifact/..../",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 200

    # Test that invalid remote uri's cannot be created
    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "qcflow-artifacts://host:9000/models/../../../",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 400
    assert "If supplying a source as an http, https," in response.json()["message"]

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "http://host:9000/models/../../../",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 400
    assert "If supplying a source as an http, https," in response.json()["message"]

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "https://host/api/2.0/qcflow-artifacts/artifacts/../../../",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 400
    assert "If supplying a source as an http, https," in response.json()["message"]

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "s3a://my_bucket/api/2.0/qcflow-artifacts/artifacts/../../../",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 400
    assert "If supplying a source as an http, https," in response.json()["message"]

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "ftp://host:8888/api/2.0/qcflow-artifacts/artifacts/../../../",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 400
    assert "If supplying a source as an http, https," in response.json()["message"]

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "qcflow-artifacts://host:9000/models/..%2f..%2fartifacts",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 400
    assert "If supplying a source as an http, https," in response.json()["message"]

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "qcflow-artifacts://host:9000/models/artifact%00",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 400
    assert "If supplying a source as an http, https," in response.json()["message"]

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": f"dbfs:/{run.info.run_id}/artifacts/a%3f/../../../../../../../../../../",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 400
    assert "Invalid model version source" in response.json()["message"]


def test_create_model_version_with_file_uri(qcflow_client):
    name = "test"
    qcflow_client.create_registered_model(name)
    exp_id = qcflow_client.create_experiment("test")
    run = qcflow_client.create_run(experiment_id=exp_id)
    assert run.info.artifact_uri.startswith("file://")
    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": run.info.artifact_uri,
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 200

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": f"{run.info.artifact_uri}/model",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 200

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": f"{run.info.artifact_uri}/.",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 200

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": f"{run.info.artifact_uri}/model/..",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 200

    # run_id is not specified
    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": run.info.artifact_uri,
        },
    )
    assert response.status_code == 400
    assert "To use a local path as a model version" in response.json()["message"]

    # run_id is specified but source is not in the run's artifact directory
    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "file:///tmp",
        },
    )
    assert response.status_code == 400
    assert "To use a local path as a model version" in response.json()["message"]

    response = requests.post(
        f"{qcflow_client.tracking_uri}/api/2.0/qcflow/model-versions/create",
        json={
            "name": name,
            "source": "file://123.456.789.123/path/to/source",
            "run_id": run.info.run_id,
        },
    )
    assert response.status_code == 500, response.json()
    assert "is not a valid remote uri" in response.json()["message"]


def test_logging_model_with_local_artifact_uri(qcflow_client):
    from sklearn.linear_model import LogisticRegression

    qcflow.set_tracking_uri(qcflow_client.tracking_uri)
    with qcflow.start_run() as run:
        assert run.info.artifact_uri.startswith("file://")
        qcflow.sklearn.log_model(LogisticRegression(), "model", registered_model_name="rmn")
        qcflow.pyfunc.load_model("models:/rmn/1")


def test_log_input(qcflow_client, tmp_path):
    df = pd.DataFrame([[1, 2, 3], [1, 2, 3]], columns=["a", "b", "c"])
    path = tmp_path / "temp.csv"
    df.to_csv(path)
    dataset = from_pandas(df, source=path)

    qcflow.set_tracking_uri(qcflow_client.tracking_uri)

    with qcflow.start_run() as run:
        qcflow.log_input(dataset, "train", {"foo": "baz"})

    dataset_inputs = qcflow_client.get_run(run.info.run_id).inputs.dataset_inputs

    assert len(dataset_inputs) == 1
    assert dataset_inputs[0].dataset.name == "dataset"
    assert dataset_inputs[0].dataset.digest == "f0f3e026"
    assert dataset_inputs[0].dataset.source_type == "local"
    assert json.loads(dataset_inputs[0].dataset.source) == {"uri": str(path)}
    assert json.loads(dataset_inputs[0].dataset.schema) == {
        "qcflow_colspec": [
            {"name": "a", "type": "long", "required": True},
            {"name": "b", "type": "long", "required": True},
            {"name": "c", "type": "long", "required": True},
        ]
    }
    assert json.loads(dataset_inputs[0].dataset.profile) == {"num_rows": 2, "num_elements": 6}

    assert len(dataset_inputs[0].tags) == 2
    assert dataset_inputs[0].tags[0].key == "foo"
    assert dataset_inputs[0].tags[0].value == "baz"
    assert dataset_inputs[0].tags[1].key == qcflow_tags.QCFLOW_DATASET_CONTEXT
    assert dataset_inputs[0].tags[1].value == "train"


def test_log_inputs(qcflow_client):
    experiment_id = qcflow_client.create_experiment("log inputs test")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id

    dataset1 = Dataset(
        name="name1",
        digest="digest1",
        source_type="source_type1",
        source="source1",
    )
    dataset_inputs1 = [DatasetInput(dataset=dataset1, tags=[InputTag(key="tag1", value="value1")])]

    qcflow_client.log_inputs(run_id, dataset_inputs1)
    run = qcflow_client.get_run(run_id)
    assert len(run.inputs.dataset_inputs) == 1

    assert isinstance(run.inputs, RunInputs)
    assert isinstance(run.inputs.dataset_inputs[0], DatasetInput)
    assert isinstance(run.inputs.dataset_inputs[0].dataset, Dataset)
    assert run.inputs.dataset_inputs[0].dataset.name == "name1"
    assert run.inputs.dataset_inputs[0].dataset.digest == "digest1"
    assert run.inputs.dataset_inputs[0].dataset.source_type == "source_type1"
    assert run.inputs.dataset_inputs[0].dataset.source == "source1"
    assert len(run.inputs.dataset_inputs[0].tags) == 1
    assert run.inputs.dataset_inputs[0].tags[0].key == "tag1"
    assert run.inputs.dataset_inputs[0].tags[0].value == "value1"


def test_log_inputs_validation(qcflow_client):
    experiment_id = qcflow_client.create_experiment("log inputs validation")
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id

    def assert_bad_request(payload, expected_error_message):
        response = _send_rest_tracking_post_request(
            qcflow_client.tracking_uri,
            "/api/2.0/qcflow/runs/log-inputs",
            payload,
        )
        assert response.status_code == 400
        assert expected_error_message in response.text

    dataset = Dataset(
        name="name1",
        digest="digest1",
        source_type="source_type1",
        source="source1",
    )
    tags = [InputTag(key="tag1", value="value1")]
    dataset_inputs = [
        json.loads(message_to_json(DatasetInput(dataset=dataset, tags=tags).to_proto()))
    ]
    assert_bad_request(
        {
            "datasets": dataset_inputs,
        },
        "Missing value for required parameter 'run_id'",
    )
    assert_bad_request(
        {
            "run_id": run_id,
        },
        "Missing value for required parameter 'datasets'",
    )


def test_update_run_name_without_changing_status(qcflow_client):
    experiment_id = qcflow_client.create_experiment("update run name")
    created_run = qcflow_client.create_run(experiment_id)
    qcflow_client.set_terminated(created_run.info.run_id, "FINISHED")

    qcflow_client.update_run(created_run.info.run_id, name="name_abc")
    updated_run_info = qcflow_client.get_run(created_run.info.run_id).info
    assert updated_run_info.run_name == "name_abc"
    assert updated_run_info.status == "FINISHED"


def test_create_promptlab_run_handler_rejects_invalid_requests(qcflow_client):
    def assert_response(resp, message_part):
        assert resp.status_code == 400
        response_json = resp.json()
        assert response_json.get("error_code") == "INVALID_PARAMETER_VALUE"
        assert message_part in response_json.get("message", "")

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/runs/create-promptlab-run",
        json={},
    )
    assert_response(
        response,
        "CreatePromptlabRun request must specify experiment_id.",
    )

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/runs/create-promptlab-run",
        json={"experiment_id": "123"},
    )
    assert_response(
        response,
        "CreatePromptlabRun request must specify prompt_template.",
    )

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/runs/create-promptlab-run",
        json={"experiment_id": "123", "prompt_template": "my_prompt_template"},
    )
    assert_response(
        response,
        "CreatePromptlabRun request must specify prompt_parameters.",
    )

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/runs/create-promptlab-run",
        json={
            "experiment_id": "123",
            "prompt_template": "my_prompt_template",
            "prompt_parameters": [{"key": "my_key", "value": "my_value"}],
        },
    )
    assert_response(
        response,
        "CreatePromptlabRun request must specify model_route.",
    )

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/runs/create-promptlab-run",
        json={
            "experiment_id": "123",
            "prompt_template": "my_prompt_template",
            "prompt_parameters": [{"key": "my_key", "value": "my_value"}],
            "model_route": "my_route",
        },
    )
    assert_response(
        response,
        "CreatePromptlabRun request must specify model_input.",
    )

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/runs/create-promptlab-run",
        json={
            "experiment_id": "123",
            "prompt_template": "my_prompt_template",
            "prompt_parameters": [{"key": "my_key", "value": "my_value"}],
            "model_route": "my_route",
            "model_input": "my_input",
        },
    )
    assert_response(
        response,
        "CreatePromptlabRun request must specify qcflow_version.",
    )

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/runs/create-promptlab-run",
        json={
            "experiment_id": "123",
            "prompt_template": "my_prompt_template",
            "prompt_parameters": [{"key": "my_key", "value": "my_value"}],
            "model_route": "my_route",
            "model_input": "my_input",
            "qcflow_version": "1.0.0",
        },
    )


def test_create_promptlab_run_handler_returns_expected_results(qcflow_client):
    experiment_id = qcflow_client.create_experiment("log inputs test")

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/runs/create-promptlab-run",
        json={
            "experiment_id": experiment_id,
            "run_name": "my_run_name",
            "prompt_template": "my_prompt_template",
            "prompt_parameters": [{"key": "my_key", "value": "my_value"}],
            "model_route": "my_route",
            "model_parameters": [{"key": "temperature", "value": "0.1"}],
            "model_input": "my_input",
            "model_output": "my_output",
            "model_output_parameters": [{"key": "latency", "value": "100"}],
            "qcflow_version": "1.0.0",
            "user_id": "username",
            "start_time": 456,
        },
    )
    assert response.status_code == 200
    run_json = response.json()
    assert run_json["run"]["info"]["run_name"] == "my_run_name"
    assert run_json["run"]["info"]["experiment_id"] == experiment_id
    assert run_json["run"]["info"]["user_id"] == "username"
    assert run_json["run"]["info"]["status"] == "FINISHED"
    assert run_json["run"]["info"]["start_time"] == 456

    assert {"key": "model_route", "value": "my_route"} in run_json["run"]["data"]["params"]
    assert {"key": "prompt_template", "value": "my_prompt_template"} in run_json["run"]["data"][
        "params"
    ]
    assert {"key": "temperature", "value": "0.1"} in run_json["run"]["data"]["params"]

    assert {
        "key": "qcflow.loggedArtifacts",
        "value": '[{"path": "eval_results_table.json", "type": "table"}]',
    } in run_json["run"]["data"]["tags"]
    assert {"key": "qcflow.runSourceType", "value": "PROMPT_ENGINEERING"} in run_json["run"][
        "data"
    ]["tags"]


def test_gateway_proxy_handler_rejects_invalid_requests(qcflow_client):
    def assert_response(resp, message_part):
        assert resp.status_code == 400
        response_json = resp.json()
        assert response_json.get("error_code") == "INVALID_PARAMETER_VALUE"
        assert message_part in response_json.get("message", "")

    with _init_server(
        backend_uri=qcflow_client.tracking_uri,
        root_artifact_uri=qcflow_client.tracking_uri,
        extra_env={"QCFLOW_DEPLOYMENTS_TARGET": "http://localhost:5001"},
    ) as url:
        patched_client = MlflowClient(url)

        response = requests.post(
            f"{patched_client.tracking_uri}/ajax-api/2.0/qcflow/gateway-proxy",
            json={},
        )
        assert_response(
            response,
            "Deployments proxy request must specify a gateway_path.",
        )


def test_upload_artifact_handler_rejects_invalid_requests(qcflow_client):
    def assert_response(resp, message_part):
        assert resp.status_code == 400
        response_json = resp.json()
        assert response_json.get("error_code") == "INVALID_PARAMETER_VALUE"
        assert message_part in response_json.get("message", "")

    experiment_id = qcflow_client.create_experiment("upload_artifacts_test")
    created_run = qcflow_client.create_run(experiment_id)

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/upload-artifact", params={}
    )
    assert_response(response, "Request must specify run_uuid.")

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/upload-artifact",
        params={
            "run_uuid": created_run.info.run_id,
        },
    )
    assert_response(response, "Request must specify path.")

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/upload-artifact",
        params={"run_uuid": created_run.info.run_id, "path": ""},
    )
    assert_response(response, "Request must specify path.")

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/upload-artifact",
        params={"run_uuid": created_run.info.run_id, "path": "../test.txt"},
    )
    assert_response(response, "Invalid path")

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/upload-artifact",
        params={
            "run_uuid": created_run.info.run_id,
            "path": "test.txt",
        },
    )
    assert_response(response, "Request must specify data.")


def test_upload_artifact_handler(qcflow_client):
    experiment_id = qcflow_client.create_experiment("upload_artifacts_test")
    created_run = qcflow_client.create_run(experiment_id)

    response = requests.post(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/upload-artifact",
        params={
            "run_uuid": created_run.info.run_id,
            "path": "test.txt",
        },
        data="hello world",
    )
    assert response.status_code == 200

    response = requests.get(
        f"{qcflow_client.tracking_uri}/get-artifact",
        params={
            "run_uuid": created_run.info.run_id,
            "path": "test.txt",
        },
    )
    assert response.status_code == 200
    assert response.text == "hello world"


def test_graphql_handler(qcflow_client):
    response = requests.post(
        f"{qcflow_client.tracking_uri}/graphql",
        json={
            "query": 'query testQuery {test(inputString: "abc") { output }}',
            "operationName": "testQuery",
        },
        headers={"content-type": "application/json; charset=utf-8"},
    )
    assert response.status_code == 200


def test_get_experiment_graphql(qcflow_client):
    experiment_id = qcflow_client.create_experiment("GraphqlTest")
    response = requests.post(
        f"{qcflow_client.tracking_uri}/graphql",
        json={
            "query": 'query testQuery {qcflowGetExperiment(input: {experimentId: "'
            + experiment_id
            + '"}) { experiment { name } }}',
            "operationName": "testQuery",
        },
        headers={"content-type": "application/json; charset=utf-8"},
    )
    assert response.status_code == 200
    json = response.json()
    assert json["data"]["qcflowGetExperiment"]["experiment"]["name"] == "GraphqlTest"


def test_get_run_and_experiment_graphql(qcflow_client):
    name = "GraphqlTest"
    qcflow_client.create_registered_model(name)
    experiment_id = qcflow_client.create_experiment(name)
    created_run = qcflow_client.create_run(experiment_id)
    run_id = created_run.info.run_id
    qcflow_client.create_model_version("GraphqlTest", "runs:/graphql_test/model", run_id)
    response = requests.post(
        f"{qcflow_client.tracking_uri}/graphql",
        json={
            "query": f"""
                query testQuery @component(name: "Test") {{
                    qcflowGetRun(input: {{runId: "{run_id}"}}) {{
                        run {{
                            info {{
                                status
                            }}
                            experiment {{
                                name
                            }}
                            modelVersions {{
                                name
                            }}
                        }}
                    }}
                }}
            """,
            "operationName": "testQuery",
        },
        headers={"content-type": "application/json; charset=utf-8"},
    )
    assert response.status_code == 200
    json = response.json()
    assert json["errors"] is None
    assert json["data"]["qcflowGetRun"]["run"]["info"]["status"] == created_run.info.status
    assert json["data"]["qcflowGetRun"]["run"]["experiment"]["name"] == name
    assert json["data"]["qcflowGetRun"]["run"]["modelVersions"][0]["name"] == name


def test_start_and_end_trace(qcflow_client):
    experiment_id = qcflow_client.create_experiment("start end trace")

    # Trace CRUD APIs are not directly exposed as public API of MlflowClient,
    # so we use the underlying tracking client to test them.
    client = qcflow_client._tracking_client

    # Helper function to remove auto-added system tags (qcflow.xxx) from testing
    def _exclude_system_tags(tags: dict[str, str]):
        return {k: v for k, v in tags.items() if not k.startswith("qcflow.")}

    trace_info = client.start_trace(
        experiment_id=experiment_id,
        timestamp_ms=1000,
        request_metadata={
            "meta1": "apple",
            "meta2": "grape",
        },
        tags={
            "tag1": "football",
            "tag2": "basketball",
        },
    )
    assert trace_info.request_id is not None
    assert trace_info.experiment_id == experiment_id
    assert trace_info.timestamp_ms == 1000
    assert trace_info.execution_time_ms == 0
    assert trace_info.status == TraceStatus.IN_PROGRESS
    assert trace_info.request_metadata == {
        "meta1": "apple",
        "meta2": "grape",
    }
    assert _exclude_system_tags(trace_info.tags) == {
        "tag1": "football",
        "tag2": "basketball",
    }

    trace_info = client.end_trace(
        request_id=trace_info.request_id,
        timestamp_ms=3000,
        status=TraceStatus.OK,
        request_metadata={
            "meta1": "orange",
            "meta3": "banana",
        },
        tags={
            "tag1": "soccer",
            "tag3": "tennis",
        },
    )
    assert trace_info.request_id is not None
    assert trace_info.experiment_id == experiment_id
    assert trace_info.timestamp_ms == 1000
    assert trace_info.execution_time_ms == 2000
    assert trace_info.status == TraceStatus.OK
    assert trace_info.request_metadata == {
        "meta1": "orange",
        "meta2": "grape",
        "meta3": "banana",
    }
    assert _exclude_system_tags(trace_info.tags) == {
        "tag1": "soccer",
        "tag2": "basketball",
        "tag3": "tennis",
    }

    assert trace_info == client.get_trace_info(trace_info.request_id)


def test_start_and_end_trace_non_string_name(qcflow_client):
    # OpenTelemetry span can accept non-string name like 1234. However, it is problematic
    # when we use it as a trace name (which is set from a root span name) and log it to
    # remote tracking server. Trace name is stored as qcflow.traceName tag and tag value
    # can only be string, otherwise protobuf serialization will fail. Therefore, this test
    # verifies that non-string span name is correctly handled before sending to the server.
    qcflow.set_tracking_uri(qcflow_client.tracking_uri)
    exp_id = qcflow_client.create_experiment("non-string trace")

    span = qcflow_client.start_trace(name=1234, experiment_id=exp_id)
    child_span = qcflow_client.start_span(
        name=None, request_id=span.request_id, parent_id=span.span_id
    )
    qcflow_client.end_span(
        request_id=child_span.request_id, span_id=child_span.span_id, status="OK"
    )
    qcflow_client.end_trace(request_id=span.request_id, status="OK")

    traces = qcflow_client.search_traces(experiment_ids=[exp_id])
    assert len(traces) == 1
    trace = traces[0]
    assert trace.info.tags[TraceTagKey.TRACE_NAME] == "1234"
    assert trace.info.status == TraceStatus.OK
    assert len(trace.data.spans) == 2
    assert trace.data.spans[0].name == 1234
    assert trace.data.spans[0].status.status_code == "OK"
    assert trace.data.spans[1].name is None
    assert trace.data.spans[1].status.status_code == "OK"


def test_search_traces(qcflow_client):
    qcflow.set_tracking_uri(qcflow_client.tracking_uri)
    experiment_id = qcflow_client.create_experiment("search traces")

    # Create test traces
    def _create_trace(name, status):
        span = qcflow_client.start_trace(name=name, experiment_id=experiment_id)
        qcflow_client.end_trace(request_id=span.request_id, status=status)
        return span.request_id

    request_id_1 = _create_trace(name="trace1", status=TraceStatus.OK)
    request_id_2 = _create_trace(name="trace2", status=TraceStatus.OK)
    request_id_3 = _create_trace(name="trace3", status=TraceStatus.ERROR)

    def _get_request_ids(traces):
        return [t.info.request_id for t in traces]

    # Validate search
    traces = qcflow_client.search_traces(experiment_ids=[experiment_id])
    assert _get_request_ids(traces) == [request_id_3, request_id_2, request_id_1]
    assert traces.token is None

    traces = qcflow_client.search_traces(
        experiment_ids=[experiment_id],
        filter_string="status = 'OK'",
        order_by=["timestamp ASC"],
    )
    assert _get_request_ids(traces) == [request_id_1, request_id_2]
    assert traces.token is None

    traces = qcflow_client.search_traces(
        experiment_ids=[experiment_id],
        max_results=2,
    )
    assert _get_request_ids(traces) == [request_id_3, request_id_2]
    assert traces.token is not None
    traces = qcflow_client.search_traces(
        experiment_ids=[experiment_id],
        page_token=traces.token,
    )
    assert _get_request_ids(traces) == [request_id_1]
    assert traces.token is None


def test_delete_traces(qcflow_client):
    qcflow.set_tracking_uri(qcflow_client.tracking_uri)
    experiment_id = qcflow_client.create_experiment("delete traces")

    def _create_trace(name, status):
        span = qcflow_client.start_trace(name=name, experiment_id=experiment_id)
        qcflow_client.end_trace(request_id=span.request_id, status=status)
        return span.request_id

    def _is_trace_exists(request_id):
        try:
            trace_info = qcflow_client._tracking_client.get_trace_info(request_id)
            return trace_info is not None
        except RestException as e:
            if e.error_code == ErrorCode.Name(RESOURCE_DOES_NOT_EXIST):
                return False
            raise

    # Case 1: Delete all traces under experiment ID
    request_id_1 = _create_trace(name="trace1", status=TraceStatus.OK)
    request_id_2 = _create_trace(name="trace2", status=TraceStatus.OK)
    assert _is_trace_exists(request_id_1)
    assert _is_trace_exists(request_id_2)

    deleted_count = qcflow_client.delete_traces(experiment_id, max_timestamp_millis=int(1e15))
    assert deleted_count == 2
    assert not _is_trace_exists(request_id_1)
    assert not _is_trace_exists(request_id_2)

    # Case 2: Delete with max_traces limit
    request_id_1 = _create_trace(name="trace1", status=TraceStatus.OK)
    time.sleep(0.1)  # Add some time gap to avoid timestamp collision
    request_id_2 = _create_trace(name="trace2", status=TraceStatus.OK)

    deleted_count = qcflow_client.delete_traces(
        experiment_id, max_traces=1, max_timestamp_millis=int(1e15)
    )
    assert deleted_count == 1
    # TODO: Currently the deletion order in the file store is random (based on
    # the order of the trace files in the directory), so we don't validate which
    # one is deleted. Uncomment the following lines once the deletion order is fixed.
    # assert not _is_trace_exists(request_id_1)  # Old created trace should be deleted
    # assert _is_trace_exists(request_id_2)

    # Case 3: Delete with explicit request ID
    request_id_1 = _create_trace(name="trace1", status=TraceStatus.OK)
    request_id_2 = _create_trace(name="trace2", status=TraceStatus.OK)

    deleted_count = qcflow_client.delete_traces(experiment_id, request_ids=[request_id_1])
    assert deleted_count == 1
    assert not _is_trace_exists(request_id_1)
    assert _is_trace_exists(request_id_2)


def test_set_and_delete_trace_tag(qcflow_client):
    qcflow.set_tracking_uri(qcflow_client.tracking_uri)
    experiment_id = qcflow_client.create_experiment("set delete tag")

    # Create test trace
    trace_info = qcflow_client._tracking_client.start_trace(
        experiment_id=experiment_id,
        timestamp_ms=1000,
        request_metadata={},
        tags={
            "tag1": "red",
            "tag2": "blue",
        },
    )

    # Validate set tag
    qcflow_client.set_trace_tag(trace_info.request_id, "tag1", "green")
    trace_info = qcflow_client._tracking_client.get_trace_info(trace_info.request_id)
    assert trace_info.tags["tag1"] == "green"

    # Validate delete tag
    qcflow_client.delete_trace_tag(trace_info.request_id, "tag2")
    trace_info = qcflow_client._tracking_client.get_trace_info(trace_info.request_id)
    assert "tag2" not in trace_info.tags


def test_get_trace_artifact_handler(qcflow_client):
    qcflow.set_tracking_uri(qcflow_client.tracking_uri)

    experiment_id = qcflow_client.create_experiment("get trace artifact")

    span = qcflow_client.start_trace(name="test", experiment_id=experiment_id)
    request_id = span.request_id
    span.set_attributes({"fruit": "apple"})
    qcflow_client.end_trace(request_id=request_id)

    response = requests.get(
        f"{qcflow_client.tracking_uri}/ajax-api/2.0/qcflow/get-trace-artifact",
        params={"request_id": request_id},
    )
    assert response.status_code == 200
    assert response.headers["Content-Disposition"] == "attachment; filename=traces.json"

    # Validate content
    trace_data = TraceData.from_dict(json.loads(response.text))
    assert trace_data.spans[0].to_dict() == span.to_dict()


def test_get_metric_history_bulk_interval_graphql(qcflow_client):
    name = "GraphqlTest"
    qcflow_client.create_registered_model(name)
    experiment_id = qcflow_client.create_experiment(name)
    created_run = qcflow_client.create_run(experiment_id)

    metric_name = "metric_0"
    for i in range(10):
        qcflow_client.log_metric(created_run.info.run_id, metric_name, i, step=i)

    response = requests.post(
        f"{qcflow_client.tracking_uri}/graphql",
        json={
            "query": f"""
                query testQuery {{
                    qcflowGetMetricHistoryBulkInterval(input: {{
                        runIds: ["{created_run.info.run_id}"],
                        metricKey: "{metric_name}",
                    }}) {{
                        metrics {{
                            key
                            timestamp
                            value
                        }}
                    }}
                }}
            """,
            "operationName": "testQuery",
        },
        headers={"content-type": "application/json; charset=utf-8"},
    )

    assert response.status_code == 200
    json = response.json()
    expected = [{"key": metric_name, "timestamp": mock.ANY, "value": i} for i in range(10)]
    assert json["data"]["qcflowGetMetricHistoryBulkInterval"]["metrics"] == expected


def test_search_runs_graphql(qcflow_client):
    name = "GraphqlTest"
    qcflow_client.create_registered_model(name)
    experiment_id = qcflow_client.create_experiment(name)
    created_run_1 = qcflow_client.create_run(experiment_id)
    created_run_2 = qcflow_client.create_run(experiment_id)

    response = requests.post(
        f"{qcflow_client.tracking_uri}/graphql",
        json={
            "query": f"""
                mutation testMutation {{
                    qcflowSearchRuns(input: {{ experimentIds: ["{experiment_id}"] }}) {{
                        runs {{
                            info {{
                                runId
                            }}
                        }}
                    }}
                }}
            """,
            "operationName": "testMutation",
        },
        headers={"content-type": "application/json; charset=utf-8"},
    )

    assert response.status_code == 200
    json = response.json()
    expected = [
        {"info": {"runId": created_run_2.info.run_id}},
        {"info": {"runId": created_run_1.info.run_id}},
    ]
    assert json["data"]["qcflowSearchRuns"]["runs"] == expected


def test_list_artifacts_graphql(qcflow_client, tmp_path):
    name = "GraphqlTest"
    experiment_id = qcflow_client.create_experiment(name)
    created_run_id = qcflow_client.create_run(experiment_id).info.run_id
    file_path = tmp_path / "test.txt"
    file_path.write_text("hello world")
    qcflow_client.log_artifact(created_run_id, file_path.absolute().as_posix())
    qcflow_client.log_artifact(created_run_id, file_path.absolute().as_posix(), "testDir")

    response = requests.post(
        f"{qcflow_client.tracking_uri}/graphql",
        json={
            "query": f"""
                fragment FilesFragment on MlflowListArtifactsResponse {{
                    files {{
                        path
                        isDir
                        fileSize
                    }}
                }}

                query testQuery {{
                    file: qcflowListArtifacts(input: {{ runId: "{created_run_id}" }}) {{
                        ...FilesFragment
                    }}
                    subdir: qcflowListArtifacts(input: {{
                        runId: "{created_run_id}",
                        path: "testDir",
                    }}) {{
                        ...FilesFragment
                    }}
                }}
            """,
            "operationName": "testQuery",
        },
        headers={"content-type": "application/json; charset=utf-8"},
    )

    assert response.status_code == 200
    json = response.json()
    file_expected = [
        {"path": "test.txt", "isDir": False, "fileSize": "11"},
        {"path": "testDir", "isDir": True, "fileSize": "0"},
    ]
    assert json["data"]["file"]["files"] == file_expected
    subdir_expected = [
        {"path": "testDir/test.txt", "isDir": False, "fileSize": "11"},
    ]
    assert json["data"]["subdir"]["files"] == subdir_expected


def test_search_datasets_graphql(qcflow_client):
    name = "GraphqlTest"
    experiment_id = qcflow_client.create_experiment(name)
    created_run_id = qcflow_client.create_run(experiment_id).info.run_id
    dataset1 = Dataset(
        name="test-dataset-1",
        digest="12345",
        source_type="script",
        source="test",
    )
    dataset_input1 = DatasetInput(dataset=dataset1, tags=[])
    dataset2 = Dataset(
        name="test-dataset-2",
        digest="12346",
        source_type="script",
        source="test",
    )
    dataset_input2 = DatasetInput(
        dataset=dataset2, tags=[InputTag(key=QCFLOW_DATASET_CONTEXT, value="training")]
    )
    qcflow_client.log_inputs(created_run_id, [dataset_input1, dataset_input2])

    response = requests.post(
        f"{qcflow_client.tracking_uri}/graphql",
        json={
            "query": f"""
                mutation testMutation {{
                    qcflowSearchDatasets(input:{{experimentIds: ["{experiment_id}"]}}) {{
                        datasetSummaries {{
                            experimentId
                            name
                            digest
                            context
                        }}
                    }}
                }}
            """,
            "operationName": "testMutation",
        },
        headers={"content-type": "application/json; charset=utf-8"},
    )

    assert response.status_code == 200
    json = response.json()

    def sort_dataset_summaries(l1):
        return sorted(l1, key=lambda x: x["digest"])

    expected = sort_dataset_summaries(
        [
            {
                "experimentId": experiment_id,
                "name": "test-dataset-2",
                "digest": "12346",
                "context": "training",
            },
            {
                "experimentId": experiment_id,
                "name": "test-dataset-1",
                "digest": "12345",
                "context": "",
            },
        ]
    )
    assert (
        sort_dataset_summaries(json["data"]["qcflowSearchDatasets"]["datasetSummaries"]) == expected
    )
