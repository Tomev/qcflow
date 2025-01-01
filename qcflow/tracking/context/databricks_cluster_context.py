from qcflow.tracking.context.abstract_context import RunContextProvider
from qcflow.utils import databricks_utils
from qcflow.utils.qcflow_tags import QCFLOW_DATABRICKS_CLUSTER_ID


class DatabricksClusterRunContext(RunContextProvider):
    def in_context(self):
        return databricks_utils.is_in_cluster()

    def tags(self):
        cluster_id = databricks_utils.get_cluster_id()
        tags = {}
        if cluster_id is not None:
            tags[QCFLOW_DATABRICKS_CLUSTER_ID] = cluster_id
        return tags
