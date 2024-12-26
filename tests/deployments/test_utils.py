import pytest

from qcflow.deployments.utils import (
    get_deployments_target,
    set_deployments_target,
)
from qcflow.exceptions import MlflowException


def test_set_deployments_target(monkeypatch):
    monkeypatch.setattr("qcflow.deployments.utils._deployments_target", None)

    valid_target = "databricks"
    set_deployments_target(valid_target)
    assert get_deployments_target() == valid_target

    valid_uri = "http://localhost"
    set_deployments_target(valid_uri)
    assert get_deployments_target() == valid_uri

    invalid_uri = "localhost"
    with pytest.raises(
        MlflowException, match="The target provided is not a valid uri or 'databricks'"
    ):
        set_deployments_target(invalid_uri)


def test_get_deployments_target(monkeypatch):
    monkeypatch.setattr("qcflow.deployments.utils._deployments_target", None)
    monkeypatch.delenv("QCFLOW_DEPLOYMENTS_TARGET", raising=False)

    with pytest.raises(MlflowException, match="No deployments target has been set"):
        get_deployments_target()

    valid_uri = "http://localhost"
    monkeypatch.setattr("qcflow.deployments.utils._deployments_target", valid_uri)
    assert get_deployments_target() == valid_uri

    monkeypatch.delenv("QCFLOW_DEPLOYMENTS_TARGET", raising=False)
    set_deployments_target(valid_uri)
    assert get_deployments_target() == valid_uri
