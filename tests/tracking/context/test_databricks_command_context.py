from unittest import mock

from qcflow.tracking.context.databricks_command_context import DatabricksCommandRunContext
from qcflow.utils.qcflow_tags import QCFLOW_DATABRICKS_NOTEBOOK_COMMAND_ID


def test_databricks_command_run_context_in_context():
    with mock.patch("qcflow.utils.databricks_utils.get_job_group_id", return_value="1"):
        assert DatabricksCommandRunContext().in_context()


def test_databricks_command_run_context_tags():
    with mock.patch("qcflow.utils.databricks_utils.get_job_group_id") as job_group_id_mock:
        assert DatabricksCommandRunContext().tags() == {
            QCFLOW_DATABRICKS_NOTEBOOK_COMMAND_ID: job_group_id_mock.return_value
        }


def test_databricks_command_run_context_tags_nones():
    with mock.patch("qcflow.utils.databricks_utils.get_job_group_id", return_value=None):
        assert DatabricksCommandRunContext().tags() == {}
