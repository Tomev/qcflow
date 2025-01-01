import os

import pytest

import qcflow


@pytest.fixture(autouse=True)
def tracking_uri_mock(tmp_path, monkeypatch):
    tracking_uri = "sqlite:///{}".format(tmp_path / "mlruns.sqlite")
    qcflow.set_tracking_uri(tracking_uri)
    monkeypatch.setenv("QCFLOW_TRACKING_URI", tracking_uri)
    yield
    qcflow.set_tracking_uri(None)


@pytest.fixture(autouse=True)
def reset_active_experiment_id():
    yield
    qcflow.tracking.fluent._active_experiment_id = None
    os.environ.pop("QCFLOW_EXPERIMENT_ID", None)


@pytest.fixture(autouse=True)
def reset_qcflow_uri():
    yield
    os.environ.pop("QCFLOW_TRACKING_URI", None)
    os.environ.pop("QCFLOW_REGISTRY_URI", None)
