from unittest import mock

import pytest

from qcflow import QCFlowClient, register_model
from qcflow.entities.model_registry import ModelVersion, RegisteredModel
from qcflow.exceptions import QCFlowException
from qcflow.protos.databricks_pb2 import (
    ALREADY_EXISTS,
    INTERNAL_ERROR,
    RESOURCE_ALREADY_EXISTS,
)
from qcflow.tracking._model_registry import DEFAULT_AWAIT_MAX_SLEEP_SECONDS


def test_register_model_with_runs_uri():
    create_model_patch = mock.patch.object(
        QCFlowClient, "create_registered_model", return_value=RegisteredModel("Model 1")
    )
    get_uri_patch = mock.patch(
        "qcflow.store.artifact.runs_artifact_repo.RunsArtifactRepository.get_underlying_uri",
        return_value="s3:/path/to/source",
    )
    create_version_patch = mock.patch.object(
        QCFlowClient,
        "_create_model_version",
        return_value=ModelVersion("Model 1", "1", creation_timestamp=123),
    )
    with get_uri_patch, create_model_patch, create_version_patch:
        register_model("runs:/run12345/path/to/model", "Model 1")
        QCFlowClient.create_registered_model.assert_called_once_with("Model 1")
        QCFlowClient._create_model_version.assert_called_once_with(
            name="Model 1",
            source="s3:/path/to/source",
            run_id="run12345",
            tags=None,
            await_creation_for=DEFAULT_AWAIT_MAX_SLEEP_SECONDS,
            local_model_path=None,
        )


def test_register_model_with_non_runs_uri():
    create_model_patch = mock.patch.object(
        QCFlowClient, "create_registered_model", return_value=RegisteredModel("Model 1")
    )
    create_version_patch = mock.patch.object(
        QCFlowClient,
        "_create_model_version",
        return_value=ModelVersion("Model 1", "1", creation_timestamp=123),
    )
    with create_model_patch, create_version_patch:
        register_model("s3:/some/path/to/model", "Model 1")
        QCFlowClient.create_registered_model.assert_called_once_with("Model 1")
        QCFlowClient._create_model_version.assert_called_once_with(
            name="Model 1",
            run_id=None,
            tags=None,
            source="s3:/some/path/to/model",
            await_creation_for=DEFAULT_AWAIT_MAX_SLEEP_SECONDS,
            local_model_path=None,
        )


@pytest.mark.parametrize("error_code", [RESOURCE_ALREADY_EXISTS, ALREADY_EXISTS])
def test_register_model_with_existing_registered_model(error_code):
    create_model_patch = mock.patch.object(
        QCFlowClient,
        "create_registered_model",
        side_effect=QCFlowException("Some Message", error_code),
    )
    create_version_patch = mock.patch.object(
        QCFlowClient,
        "_create_model_version",
        return_value=ModelVersion("Model 1", "1", creation_timestamp=123),
    )
    with create_model_patch, create_version_patch:
        register_model("s3:/some/path/to/model", "Model 1")
        QCFlowClient.create_registered_model.assert_called_once_with("Model 1")
        QCFlowClient._create_model_version.assert_called_once_with(
            name="Model 1",
            run_id=None,
            source="s3:/some/path/to/model",
            tags=None,
            await_creation_for=DEFAULT_AWAIT_MAX_SLEEP_SECONDS,
            local_model_path=None,
        )


def test_register_model_with_unexpected_qcflow_exception_in_create_registered_model():
    with mock.patch.object(
        QCFlowClient,
        "create_registered_model",
        side_effect=QCFlowException("Dunno", INTERNAL_ERROR),
    ) as mock_create_registered_model:
        with pytest.raises(QCFlowException, match="Dunno"):
            register_model("s3:/some/path/to/model", "Model 1")
        mock_create_registered_model.assert_called_once_with("Model 1")


def test_register_model_with_unexpected_exception_in_create_registered_model():
    with mock.patch.object(
        QCFlowClient, "create_registered_model", side_effect=Exception("Dunno")
    ) as create_registered_model_mock:
        with pytest.raises(Exception, match="Dunno"):
            register_model("s3:/some/path/to/model", "Model 1")
        create_registered_model_mock.assert_called_once_with("Model 1")


def test_register_model_with_tags():
    tags = {"a": 1}
    create_model_patch = mock.patch.object(
        QCFlowClient, "create_registered_model", return_value=RegisteredModel("Model 1")
    )
    get_uri_patch = mock.patch(
        "qcflow.store.artifact.runs_artifact_repo.RunsArtifactRepository.get_underlying_uri",
        return_value="s3:/path/to/source",
    )
    create_version_patch = mock.patch.object(
        QCFlowClient,
        "_create_model_version",
        return_value=ModelVersion("Model 1", "1", creation_timestamp=123),
    )
    with get_uri_patch, create_model_patch, create_version_patch:
        register_model("runs:/run12345/path/to/model", "Model 1", tags=tags)
        QCFlowClient.create_registered_model.assert_called_once_with("Model 1")
        QCFlowClient._create_model_version.assert_called_once_with(
            name="Model 1",
            source="s3:/path/to/source",
            run_id="run12345",
            tags=tags,
            await_creation_for=DEFAULT_AWAIT_MAX_SLEEP_SECONDS,
            local_model_path=None,
        )
