from qcflow.entities import SourceType
from qcflow.tracking.context.abstract_context import RunContextProvider
from qcflow.utils import databricks_utils
from qcflow.utils.qcflow_tags import (
    QCFLOW_DATABRICKS_NOTEBOOK_ID,
    QCFLOW_DATABRICKS_NOTEBOOK_PATH,
    QCFLOW_DATABRICKS_WEBAPP_URL,
    QCFLOW_DATABRICKS_WORKSPACE_ID,
    QCFLOW_DATABRICKS_WORKSPACE_URL,
    QCFLOW_SOURCE_NAME,
    QCFLOW_SOURCE_TYPE,
)


class DatabricksNotebookRunContext(RunContextProvider):
    def in_context(self):
        return databricks_utils.is_in_databricks_notebook()

    def tags(self):
        notebook_id = databricks_utils.get_notebook_id()
        notebook_path = databricks_utils.get_notebook_path()
        webapp_url = databricks_utils.get_webapp_url()
        workspace_url = databricks_utils.get_workspace_url()
        workspace_url_fallback, workspace_id = databricks_utils.get_workspace_info_from_dbutils()
        tags = {
            QCFLOW_SOURCE_NAME: notebook_path,
            QCFLOW_SOURCE_TYPE: SourceType.to_string(SourceType.NOTEBOOK),
        }
        if notebook_id is not None:
            tags[QCFLOW_DATABRICKS_NOTEBOOK_ID] = notebook_id
        if notebook_path is not None:
            tags[QCFLOW_DATABRICKS_NOTEBOOK_PATH] = notebook_path
        if webapp_url is not None:
            tags[QCFLOW_DATABRICKS_WEBAPP_URL] = webapp_url
        if workspace_url is not None:
            tags[QCFLOW_DATABRICKS_WORKSPACE_URL] = workspace_url
        elif workspace_url_fallback is not None:
            tags[QCFLOW_DATABRICKS_WORKSPACE_URL] = workspace_url_fallback
        if workspace_id is not None:
            tags[QCFLOW_DATABRICKS_WORKSPACE_ID] = workspace_id
        return tags
