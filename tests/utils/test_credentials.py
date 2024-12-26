from unittest import mock
from unittest.mock import patch

import pytest

from qcflow import get_tracking_uri
from qcflow.environment_variables import QCFLOW_TRACKING_PASSWORD, QCFLOW_TRACKING_USERNAME
from qcflow.exceptions import QCFlowException
from qcflow.utils.credentials import login, read_qcflow_creds


def test_read_qcflow_creds_file(tmp_path, monkeypatch):
    monkeypatch.delenvs(
        (QCFLOW_TRACKING_USERNAME.name, QCFLOW_TRACKING_PASSWORD.name), raising=False
    )

    creds_file = tmp_path.joinpath("credentials")
    with mock.patch("qcflow.utils.credentials._get_credentials_path", return_value=str(creds_file)):
        # credentials file does not exist
        creds = read_qcflow_creds()
        assert creds.username is None
        assert creds.password is None

        # credentials file is empty
        creds = read_qcflow_creds()
        assert creds.username is None
        assert creds.password is None

        # password is missing
        creds_file.write_text(
            """
[qcflow]
qcflow_tracking_username = username
"""
        )
        creds = read_qcflow_creds()
        assert creds.username == "username"
        assert creds.password is None

        # username is missing
        creds_file.write_text(
            """
[qcflow]
qcflow_tracking_password = password
"""
        )
        creds = read_qcflow_creds()
        assert creds.username is None
        assert creds.password == "password"

        # valid credentials
        creds_file.write_text(
            """
[qcflow]
qcflow_tracking_username = username
qcflow_tracking_password = password
"""
        )
        creds = read_qcflow_creds()
        assert creds is not None
        assert creds.username == "username"
        assert creds.password == "password"


@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("username", "password"),
        ("username", None),
        (None, "password"),
        (None, None),
    ],
)
def test_read_qcflow_creds_env(username, password, monkeypatch):
    if username is None:
        monkeypatch.delenv(QCFLOW_TRACKING_USERNAME.name, raising=False)
    else:
        monkeypatch.setenv(QCFLOW_TRACKING_USERNAME.name, username)

    if password is None:
        monkeypatch.delenv(QCFLOW_TRACKING_PASSWORD.name, raising=False)
    else:
        monkeypatch.setenv(QCFLOW_TRACKING_PASSWORD.name, password)

    creds = read_qcflow_creds()
    assert creds.username == username
    assert creds.password == password


def test_read_qcflow_creds_env_takes_precedence_over_file(tmp_path, monkeypatch):
    monkeypatch.setenv(QCFLOW_TRACKING_USERNAME.name, "username_env")
    monkeypatch.setenv(QCFLOW_TRACKING_PASSWORD.name, "password_env")
    creds_file = tmp_path.joinpath("credentials")
    with mock.patch("qcflow.utils.credentials._get_credentials_path", return_value=str(creds_file)):
        creds_file.write_text(
            """
[qcflow]
qcflow_tracking_username = username_file
qcflow_tracking_password = password_file
"""
        )
        creds = read_qcflow_creds()
        assert creds.username == "username_env"
        assert creds.password == "password_env"


def test_qcflow_login(tmp_path, monkeypatch):
    # Mock `input()` and `getpass()` to return host, username and password in order.
    with (
        patch(
            "builtins.input",
            side_effect=["https://community.cloud.databricks.com/", "dummyusername"],
        ),
        patch("getpass.getpass", side_effect=["dummypassword"]),
    ):
        file_name = f"{tmp_path}/.databrickscfg"
        profile = "TEST"
        monkeypatch.setenv("DATABRICKS_CONFIG_FILE", file_name)
        monkeypatch.setenv("DATABRICKS_CONFIG_PROFILE", profile)

        def success():
            return

        with patch(
            "qcflow.utils.credentials._validate_databricks_auth",
            side_effect=[QCFlowException("Invalid databricks credentials."), success()],
        ):
            login("databricks")

    with open(file_name) as f:
        lines = f.readlines()
        assert lines[0] == "[TEST]\n"
        assert lines[1] == "host = https://community.cloud.databricks.com/\n"
        assert lines[2] == "username = dummyusername\n"
        assert lines[3] == "password = dummypassword\n"

    # Assert that the tracking URI is set to the databricks.
    assert get_tracking_uri() == "databricks"


def test_qcflow_login_noninteractive():
    # Forces qcflow.utils.credentials._validate_databricks_auth to raise `QCFlowException()`
    with patch(
        "qcflow.utils.credentials._validate_databricks_auth",
        side_effect=QCFlowException("Failed to validate databricks credentials."),
    ):
        with pytest.raises(
            QCFlowException,
            match="No valid Databricks credentials found while running in non-interactive mode",
        ):
            login(backend="databricks", interactive=False)
