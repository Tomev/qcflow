import configparser
import getpass
import logging
import os
from typing import NamedTuple, Optional

from qcflow.environment_variables import (
    QCFLOW_TRACKING_AUTH,
    QCFLOW_TRACKING_AWS_SIGV4,
    QCFLOW_TRACKING_CLIENT_CERT_PATH,
    QCFLOW_TRACKING_INSECURE_TLS,
    QCFLOW_TRACKING_PASSWORD,
    QCFLOW_TRACKING_SERVER_CERT_PATH,
    QCFLOW_TRACKING_TOKEN,
    QCFLOW_TRACKING_USERNAME,
)
from qcflow.exceptions import QCFlowException
from qcflow.utils.rest_utils import QCFlowHostCreds

_logger = logging.getLogger(__name__)


class QCFlowCreds(NamedTuple):
    username: Optional[str]
    password: Optional[str]


def _get_credentials_path() -> str:
    return os.path.expanduser("~/.qcflow/credentials")


def _read_qcflow_creds_from_file() -> tuple[Optional[str], Optional[str]]:
    path = _get_credentials_path()
    if not os.path.exists(path):
        return None, None

    config = configparser.ConfigParser()
    config.read(path)
    if "qcflow" not in config:
        return None, None

    qcflow_cfg = config["qcflow"]
    username_key = QCFLOW_TRACKING_USERNAME.name.lower()
    password_key = QCFLOW_TRACKING_PASSWORD.name.lower()
    return qcflow_cfg.get(username_key), qcflow_cfg.get(password_key)


def _read_qcflow_creds_from_env() -> tuple[Optional[str], Optional[str]]:
    return QCFLOW_TRACKING_USERNAME.get(), QCFLOW_TRACKING_PASSWORD.get()


def read_qcflow_creds() -> QCFlowCreds:
    username_file, password_file = _read_qcflow_creds_from_file()
    username_env, password_env = _read_qcflow_creds_from_env()
    return QCFlowCreds(
        username=username_env or username_file,
        password=password_env or password_file,
    )


def get_default_host_creds(store_uri):
    creds = read_qcflow_creds()
    return QCFlowHostCreds(
        host=store_uri,
        username=creds.username,
        password=creds.password,
        token=QCFLOW_TRACKING_TOKEN.get(),
        aws_sigv4=QCFLOW_TRACKING_AWS_SIGV4.get(),
        auth=QCFLOW_TRACKING_AUTH.get(),
        ignore_tls_verification=QCFLOW_TRACKING_INSECURE_TLS.get(),
        client_cert_path=QCFLOW_TRACKING_CLIENT_CERT_PATH.get(),
        server_cert_path=QCFLOW_TRACKING_SERVER_CERT_PATH.get(),
    )


def login(backend: str = "databricks", interactive: bool = True) -> None:
    """Configure QCFlow server authentication and connect QCFlow to tracking server.

    This method provides a simple way to connect QCFlow to its tracking server. Currently only
    Databricks tracking server is supported. Users will be prompted to enter the credentials if no
    existing Databricks profile is found, and the credentials will be saved to `~/.databrickscfg`.

    Args:
        backend: string, the backend of the tracking server. Currently only "databricks" is
            supported.

        interactive: bool, controls request for user input on missing credentials. If true, user
            input will be requested if no credentials are found, otherwise an exception will be
            raised if no credentials are found.

    .. code-block:: python
        :caption: Example

        import qcflow

        qcflow.login()
        with qcflow.start_run():
            qcflow.log_param("p", 0)
    """
    from qcflow.tracking import set_tracking_uri

    if backend == "databricks":
        _databricks_login(interactive)
        set_tracking_uri("databricks")
    else:
        raise QCFlowException(
            f"Currently only 'databricks' backend is supported, received `backend={backend}`."
        )


def _validate_databricks_auth():
    # Check if databricks credentials are valid.
    try:
        from databricks.sdk import WorkspaceClient
    except ImportError:
        raise ImportError(
            "Databricks SDK is not installed. To use `qcflow.login()`, please install "
            "databricks-sdk by `pip install databricks-sdk`."
        )

    try:
        w = WorkspaceClient()
        if "community" in w.config.host:
            # Databricks community edition cannot use `w.current_user.me()` for auth validation.
            w.clusters.list_zones()
        else:
            # If credentials are invalid, `w.current_user.me()` will throw an error.
            w.current_user.me()
        _logger.info(
            f"Successfully connected to QCFlow hosted tracking server! Host: {w.config.host}."
        )
    except Exception as e:
        raise QCFlowException(f"Failed to validate databricks credentials: {e}")


def _overwrite_or_create_databricks_profile(
    file_name,
    profile,
    profile_name="DEFAULT",
):
    """Overwrite or create a profile in the databricks config file.

    Args:
        file_name: string, the file name of the databricks config file, usually `~/.databrickscfg`.
        profile: dict, contains the authentiacation profile information.
        profile_name: string, the name of the profile to be overwritten or created.
    """
    profile_name = f"[{profile_name}]"
    lines = []
    # Read `file_name` if the file exists, otherwise `lines=[]`.
    if os.path.exists(file_name):
        with open(file_name) as file:
            lines = file.readlines()
    start_index = -1
    end_index = -1
    # Find the start and end indices of the profile to overwrite.
    for i in range(len(lines)):
        if lines[i].strip() == profile_name:
            start_index = i
            break

    if start_index != -1:
        for i in range(start_index + 1, len(lines)):
            # Reach an empty line or a new profile.
            if lines[i].strip() == "" or lines[i].startswith("["):
                end_index = i
                break
        end_index = end_index if end_index != -1 else len(lines)
        del lines[start_index : end_index + 1]

    # Write the new profile to the top of the file.
    new_profile = []
    new_profile.append(profile_name + "\n")
    new_profile.append(f"host = {profile['host']}\n")
    if "token" in profile:
        new_profile.append(f"token = {profile['token']}\n")
    else:
        new_profile.append(f"username = {profile['username']}\n")
        new_profile.append(f"password = {profile['password']}\n")
    new_profile.append("\n")
    lines = new_profile + lines

    # Write back the modified lines to the file.
    with open(file_name, "w") as file:
        file.writelines(lines)


def _databricks_login(interactive):
    """Set up databricks authentication."""
    try:
        # Failed validation will throw an error.
        _validate_databricks_auth()
        return
    except Exception:
        if interactive:
            _logger.info("No valid Databricks credentials found, please enter your credentials...")
        else:
            raise QCFlowException(
                "No valid Databricks credentials found while running in non-interactive mode."
            )

    while True:
        host = input("Databricks Host (should begin with https://): ")
        if not host.startswith("https://"):
            _logger.error("Invalid host: {host}, host must begin with https://, please retry.")
        break

    profile = {"host": host}
    if "community" in host:
        # Databricks community edition requires username and password for authentication.
        username = input("Username: ")
        password = getpass.getpass("Password: ")
        profile["username"] = username
        profile["password"] = password
    else:
        # Production or staging Databricks requires personal token for authentication.
        token = getpass.getpass("Token: ")
        profile["token"] = token

    file_name = os.environ.get(
        "DATABRICKS_CONFIG_FILE", f"{os.path.expanduser('~')}/.databrickscfg"
    )
    profile_name = os.environ.get("DATABRICKS_CONFIG_PROFILE", "DEFAULT")
    _overwrite_or_create_databricks_profile(file_name, profile, profile_name)

    try:
        # Failed validation will throw an error.
        _validate_databricks_auth()
    except Exception as e:
        # If user entered invalid auth, we will raise an error and ask users to retry.
        raise QCFlowException(f"`qcflow.login()` failed with error: {e}")
