import os
from unittest import mock

import pytest

from qcflow.store.artifact.artifact_repository_registry import get_artifact_repository
from qcflow.store.artifact.dbfs_artifact_repo import (
    DatabricksArtifactRepository,
    DbfsRestArtifactRepository,
)
from qcflow.store.artifact.local_artifact_repo import LocalArtifactRepository
from qcflow.utils.rest_utils import QCFlowHostCreds


@pytest.fixture
def host_creds_mock():
    with mock.patch(
        "qcflow.store.artifact.dbfs_artifact_repo._get_host_creds_from_default_store",
        return_value=lambda: QCFlowHostCreds("http://host"),
    ):
        yield


@mock.patch("qcflow.utils.databricks_utils.is_dbfs_fuse_available")
def test_dbfs_artifact_repo_delegates_to_correct_repo(
    is_dbfs_fuse_available, host_creds_mock, monkeypatch
):
    # fuse available
    is_dbfs_fuse_available.return_value = True
    artifact_uri = "dbfs:/databricks/my/absolute/dbfs/path"
    repo = get_artifact_repository(artifact_uri)
    assert isinstance(repo, LocalArtifactRepository)
    assert repo.artifact_dir == os.path.join(
        os.path.sep, "dbfs", "databricks", "my", "absolute", "dbfs", "path"
    )
    # fuse available but a model repository DBFS location
    repo = get_artifact_repository("dbfs:/databricks/qcflow-registry/version12345/models")
    assert isinstance(repo, DbfsRestArtifactRepository)
    # fuse not available
    with monkeypatch.context() as m:
        m.setenv("QCFLOW_ENABLE_DBFS_FUSE_ARTIFACT_REPO", "false")
        fuse_disabled_repo = get_artifact_repository(artifact_uri)
    assert isinstance(fuse_disabled_repo, DbfsRestArtifactRepository)
    assert fuse_disabled_repo.artifact_uri == artifact_uri
    is_dbfs_fuse_available.return_value = False
    rest_repo = get_artifact_repository(artifact_uri)
    assert isinstance(rest_repo, DbfsRestArtifactRepository)
    assert rest_repo.artifact_uri == artifact_uri

    mock_uri = "dbfs:/databricks/qcflow-tracking/MOCK-EXP/MOCK-RUN-ID/artifacts"
    with mock.patch(
        "qcflow.store.artifact.databricks_artifact_repo"
        + ".DatabricksArtifactRepository._get_run_artifact_root",
        return_value=mock_uri,
    ):
        databricks_repo = get_artifact_repository(mock_uri)
        assert isinstance(databricks_repo, DatabricksArtifactRepository)
        assert databricks_repo.artifact_uri == mock_uri
