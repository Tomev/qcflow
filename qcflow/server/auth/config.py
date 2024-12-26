import configparser
from pathlib import Path
from typing import NamedTuple

from qcflow.environment_variables import QCFLOW_AUTH_CONFIG_PATH


class AuthConfig(NamedTuple):
    default_permission: str
    database_uri: str
    admin_username: str
    admin_password: str
    authorization_function: str


def _get_auth_config_path() -> str:
    return (
        QCFLOW_AUTH_CONFIG_PATH.get() or Path(__file__).parent.joinpath("basic_auth.ini").resolve()
    )


def read_auth_config() -> AuthConfig:
    config_path = _get_auth_config_path()
    config = configparser.ConfigParser()
    config.read(config_path)
    return AuthConfig(
        default_permission=config["qcflow"]["default_permission"],
        database_uri=config["qcflow"]["database_uri"],
        admin_username=config["qcflow"]["admin_username"],
        admin_password=config["qcflow"]["admin_password"],
        authorization_function=config["qcflow"].get(
            "authorization_function", "qcflow.server.auth:authenticate_request_basic_auth"
        ),
    )
