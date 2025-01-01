from qcflow.entities import SourceType
from qcflow.tracking.context.abstract_context import RunContextProvider
from qcflow.utils import databricks_utils
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


class DatabricksJobRunContext(RunContextProvider):
    def in_context(self):
        return databricks_utils.is_in_databricks_job()

    def tags(self):
        job_id = databricks_utils.get_job_id()
        job_run_id = databricks_utils.get_job_run_id()
        job_type = databricks_utils.get_job_type()
        webapp_url = databricks_utils.get_webapp_url()
        workspace_url = databricks_utils.get_workspace_url()
        workspace_url_fallback, workspace_id = databricks_utils.get_workspace_info_from_dbutils()
        tags = {
            QCFLOW_SOURCE_NAME: (
                f"jobs/{job_id}/run/{job_run_id}"
                if job_id is not None and job_run_id is not None
                else None
            ),
            QCFLOW_SOURCE_TYPE: SourceType.to_string(SourceType.JOB),
        }
        if job_id is not None:
            tags[QCFLOW_DATABRICKS_JOB_ID] = job_id
        if job_run_id is not None:
            tags[QCFLOW_DATABRICKS_JOB_RUN_ID] = job_run_id
        if job_type is not None:
            tags[QCFLOW_DATABRICKS_JOB_TYPE] = job_type
        if webapp_url is not None:
            tags[QCFLOW_DATABRICKS_WEBAPP_URL] = webapp_url
        if workspace_url is not None:
            tags[QCFLOW_DATABRICKS_WORKSPACE_URL] = workspace_url
        elif workspace_url_fallback is not None:
            tags[QCFLOW_DATABRICKS_WORKSPACE_URL] = workspace_url_fallback
        if workspace_id is not None:
            tags[QCFLOW_DATABRICKS_WORKSPACE_ID] = workspace_id
        return tags
