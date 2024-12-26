import urllib.parse

from qcflow.environment_variables import QCFLOW_UC_OSS_TOKEN
from qcflow.exceptions import QCFlowException
from qcflow.utils.databricks_utils import get_databricks_host_creds
from qcflow.utils.rest_utils import QCFlowHostCreds
from qcflow.utils.uri import (
    _DATABRICKS_UNITY_CATALOG_SCHEME,
)


def get_oss_host_creds(server_uri=None):
    """
    Retrieve the host credentials for the OSS server.

    Args:
        server_uri (str): The URI of the server.

    Returns:
        QCFlowHostCreds: The host credentials for the OSS server.
    """
    parsed_uri = urllib.parse.urlparse(server_uri)

    if parsed_uri.scheme != "uc":
        raise QCFlowException("The scheme of the server_uri should be 'uc'")

    if parsed_uri.path == _DATABRICKS_UNITY_CATALOG_SCHEME:
        return get_databricks_host_creds(parsed_uri.path)
    return QCFlowHostCreds(host=parsed_uri.path, token=QCFLOW_UC_OSS_TOKEN.get())
