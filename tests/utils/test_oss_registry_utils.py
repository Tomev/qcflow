from unittest import mock

import pytest

from qcflow.exceptions import QCFlowException
from qcflow.utils.oss_registry_utils import get_oss_host_creds
from qcflow.utils.rest_utils import QCFlowHostCreds


@pytest.mark.parametrize(
    ("server_uri", "expected_creds"),
    [
        ("uc:databricks-uc", QCFlowHostCreds(host="databricks-uc")),
        ("uc:http://localhost:8081", QCFlowHostCreds(host="http://localhost:8081")),
        ("invalid_scheme:http://localhost:8081", QCFlowException),
        ("databricks-uc", QCFlowException),
    ],
)
def test_get_oss_host_creds(server_uri, expected_creds):
    with mock.patch(
        "qcflow.utils.oss_registry_utils.get_databricks_host_creds",
        return_value=QCFlowHostCreds(host="databricks-uc"),
    ):
        if expected_creds == QCFlowException:
            with pytest.raises(
                QCFlowException, match="The scheme of the server_uri should be 'uc'"
            ):
                get_oss_host_creds(server_uri)
        else:
            actual_creds = get_oss_host_creds(server_uri)
            assert actual_creds == expected_creds


def test_get_databricks_host_creds():
    # Test case: When the scheme is "uc" and the new scheme is "_DATABRICKS_UNITY_CATALOG_SCHEME"
    server_uri = "uc:databricks-uc"
    with mock.patch(
        "qcflow.utils.oss_registry_utils.get_databricks_host_creds", return_value=mock.MagicMock()
    ) as mock_get_databricks_host_creds:
        get_oss_host_creds(server_uri)
        assert mock_get_databricks_host_creds.call_args_list == [mock.call("databricks-uc")]
