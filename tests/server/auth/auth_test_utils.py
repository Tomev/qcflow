from typing import Optional

from qcflow.environment_variables import QCFLOW_TRACKING_PASSWORD, QCFLOW_TRACKING_USERNAME
from qcflow.server.auth import auth_config

from tests.helper_functions import random_str
from tests.tracking.integration_test_utils import _send_rest_tracking_post_request

PERMISSION = "READ"
NEW_PERMISSION = "EDIT"
ADMIN_USERNAME = auth_config.admin_username
ADMIN_PASSWORD = auth_config.admin_password


def create_user(tracking_uri: str, username: Optional[str] = None, password: Optional[str] = None):
    username = random_str() if username is None else username
    password = random_str() if password is None else password
    response = _send_rest_tracking_post_request(
        tracking_uri,
        "/api/2.0/qcflow/users/create",
        {
            "username": username,
            "password": password,
        },
        auth=(ADMIN_USERNAME, ADMIN_PASSWORD),
    )
    response.raise_for_status()
    return username, password


class User:
    def __init__(self, username, password, monkeypatch):
        self.username = username
        self.password = password
        self.monkeypatch = monkeypatch

    def __enter__(self):
        self.monkeypatch.setenvs(
            {
                QCFLOW_TRACKING_USERNAME.name: self.username,
                QCFLOW_TRACKING_PASSWORD.name: self.password,
            }
        )

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.monkeypatch.delenvs(
            [QCFLOW_TRACKING_PASSWORD.name, QCFLOW_TRACKING_PASSWORD.name], raising=False
        )
