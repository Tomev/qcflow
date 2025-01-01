from unittest import mock

from qcflow import QCFlowClient
from qcflow.exceptions import QCFlowException
from qcflow.protos.databricks_pb2 import INVALID_PARAMETER_VALUE
from qcflow.tracking.default_experiment.databricks_notebook_experiment_provider import (
    DatabricksNotebookExperimentProvider,
)
from qcflow.utils.qcflow_tags import QCFLOW_EXPERIMENT_SOURCE_ID, QCFLOW_EXPERIMENT_SOURCE_TYPE


def test_databricks_notebook_default_experiment_in_context():
    with mock.patch("qcflow.utils.databricks_utils.is_in_databricks_notebook") as in_notebook_mock:
        assert DatabricksNotebookExperimentProvider().in_context() == in_notebook_mock.return_value


def test_databricks_notebook_default_experiment_id():
    with (
        mock.patch.object(
            QCFlowClient,
            "create_experiment",
            side_effect=QCFlowException(
                message="Error message", error_code=INVALID_PARAMETER_VALUE
            ),
        ),
        mock.patch(
            "qcflow.utils.databricks_utils.get_notebook_path",
            return_value="path",
        ),
        mock.patch("qcflow.utils.databricks_utils.get_notebook_id") as patch_notebook_id,
    ):
        assert (
            DatabricksNotebookExperimentProvider().get_experiment_id()
            == patch_notebook_id.return_value
        )


def test_databricks_repo_notebook_default_experiment_gets_id_by_request():
    with (
        mock.patch(
            "qcflow.utils.databricks_utils.get_notebook_id",
            return_value=1234,
        ),
        mock.patch(
            "qcflow.utils.databricks_utils.get_notebook_path",
            return_value="/Repos/path",
        ),
        mock.patch.object(
            QCFlowClient, "create_experiment", return_value="experiment_id"
        ) as create_experiment_mock,
    ):
        DatabricksNotebookExperimentProvider._resolved_notebook_experiment_id = None
        returned_id = DatabricksNotebookExperimentProvider().get_experiment_id()
        assert returned_id == "experiment_id"
        tags = {QCFLOW_EXPERIMENT_SOURCE_TYPE: "REPO_NOTEBOOK", QCFLOW_EXPERIMENT_SOURCE_ID: 1234}
        create_experiment_mock.assert_called_once_with("/Repos/path", None, tags)


def test_databricks_repo_notebook_default_experiment_uses_fallback_notebook_id():
    with (
        mock.patch(
            "qcflow.utils.databricks_utils.get_notebook_id",
            return_value=1234,
        ),
        mock.patch(
            "qcflow.utils.databricks_utils.get_notebook_path",
            return_value="/Repos/path",
        ),
        mock.patch.object(QCFlowClient, "create_experiment") as create_experiment_mock,
    ):
        DatabricksNotebookExperimentProvider._resolved_notebook_experiment_id = None
        create_experiment_mock.side_effect = QCFlowException(
            message="not enabled", error_code=INVALID_PARAMETER_VALUE
        )
        returned_id = DatabricksNotebookExperimentProvider().get_experiment_id()
        assert returned_id == 1234
