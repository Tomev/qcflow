from unittest import mock

from qcflow.entities import SourceType
from qcflow.tracking.context.databricks_job_context import DatabricksJobRunContext
from qcflow.utils.qcflow_tags import (
    QCFLOW_DATABRICKS_JOB_ID,
    QCFLOW_DATABRICKS_JOB_RUN_ID,
    QCFLOW_DATABRICKS_JOB_TYPE,
    QCFLOW_DATABRICKS_WEBAPP_URL,
    QCFLOW_DATABRICKS_WORKSPACE_ID,
    QCFLOW_DATABRICKS_WORKSPACE_URL,
    QCFLOW_SOURCE_NAME,
    QCFLOW_SOURCE_TYPE,
)

from tests.helper_functions import multi_context


def test_databricks_job_run_context_in_context():
    with mock.patch("qcflow.utils.databricks_utils.is_in_databricks_job") as in_job_mock:
        assert DatabricksJobRunContext().in_context() == in_job_mock.return_value


def test_databricks_job_run_context_tags():
    patch_job_id = mock.patch("qcflow.utils.databricks_utils.get_job_id")
    patch_job_run_id = mock.patch("qcflow.utils.databricks_utils.get_job_run_id")
    patch_job_type = mock.patch("qcflow.utils.databricks_utils.get_job_type")
    patch_webapp_url = mock.patch("qcflow.utils.databricks_utils.get_webapp_url")
    patch_workspace_url = mock.patch(
        "qcflow.utils.databricks_utils.get_workspace_url",
        return_value="https://dev.databricks.com",
    )
    patch_workspace_url_none = mock.patch(
        "qcflow.utils.databricks_utils.get_workspace_url", return_value=None
    )
    patch_workspace_info = mock.patch(
        "qcflow.utils.databricks_utils.get_workspace_info_from_dbutils",
        return_value=("https://databricks.com", "123456"),
    )

    with multi_context(
        patch_job_id,
        patch_job_run_id,
        patch_job_type,
        patch_webapp_url,
        patch_workspace_url,
        patch_workspace_info,
    ) as (
        job_id_mock,
        job_run_id_mock,
        job_type_mock,
        webapp_url_mock,
        workspace_url_mock,
        workspace_info_mock,
    ):
        assert DatabricksJobRunContext().tags() == {
            QCFLOW_SOURCE_NAME: (
                f"jobs/{job_id_mock.return_value}/run/{job_run_id_mock.return_value}"
            ),
            QCFLOW_SOURCE_TYPE: SourceType.to_string(SourceType.JOB),
            QCFLOW_DATABRICKS_JOB_ID: job_id_mock.return_value,
            QCFLOW_DATABRICKS_JOB_RUN_ID: job_run_id_mock.return_value,
            QCFLOW_DATABRICKS_JOB_TYPE: job_type_mock.return_value,
            QCFLOW_DATABRICKS_WEBAPP_URL: webapp_url_mock.return_value,
            QCFLOW_DATABRICKS_WORKSPACE_URL: workspace_url_mock.return_value,
            QCFLOW_DATABRICKS_WORKSPACE_ID: workspace_info_mock.return_value[1],
        }

    with multi_context(
        patch_job_id,
        patch_job_run_id,
        patch_job_type,
        patch_webapp_url,
        patch_workspace_url_none,
        patch_workspace_info,
    ) as (
        job_id_mock,
        job_run_id_mock,
        job_type_mock,
        webapp_url_mock,
        workspace_url_mock,
        workspace_info_mock,
    ):
        assert DatabricksJobRunContext().tags() == {
            QCFLOW_SOURCE_NAME: (
                f"jobs/{job_id_mock.return_value}/run/{job_run_id_mock.return_value}"
            ),
            QCFLOW_SOURCE_TYPE: SourceType.to_string(SourceType.JOB),
            QCFLOW_DATABRICKS_JOB_ID: job_id_mock.return_value,
            QCFLOW_DATABRICKS_JOB_RUN_ID: job_run_id_mock.return_value,
            QCFLOW_DATABRICKS_JOB_TYPE: job_type_mock.return_value,
            QCFLOW_DATABRICKS_WEBAPP_URL: webapp_url_mock.return_value,
            QCFLOW_DATABRICKS_WORKSPACE_URL: workspace_info_mock.return_value[0],  # fallback value
            QCFLOW_DATABRICKS_WORKSPACE_ID: workspace_info_mock.return_value[1],
        }


def test_databricks_job_run_context_tags_nones():
    patch_job_id = mock.patch("qcflow.utils.databricks_utils.get_job_id", return_value=None)
    patch_job_run_id = mock.patch("qcflow.utils.databricks_utils.get_job_run_id", return_value=None)
    patch_job_type = mock.patch("qcflow.utils.databricks_utils.get_job_type", return_value=None)
    patch_webapp_url = mock.patch("qcflow.utils.databricks_utils.get_webapp_url", return_value=None)
    patch_workspace_info = mock.patch(
        "qcflow.utils.databricks_utils.get_workspace_info_from_dbutils", return_value=(None, None)
    )

    with patch_job_id, patch_job_run_id, patch_job_type, patch_webapp_url, patch_workspace_info:
        assert DatabricksJobRunContext().tags() == {
            QCFLOW_SOURCE_NAME: None,
            QCFLOW_SOURCE_TYPE: SourceType.to_string(SourceType.JOB),
        }
