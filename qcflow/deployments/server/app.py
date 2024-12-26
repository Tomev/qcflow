"""
TODO: Remove this module once after Deployments Server deprecation window elapses
"""

from qcflow.environment_variables import (
    QCFLOW_DEPLOYMENTS_CONFIG,
)
from qcflow.exceptions import QCFlowException
from qcflow.gateway.app import GatewayAPI
from qcflow.gateway.app import (
    create_app_from_config as gateway_create_app_from_config,
)
from qcflow.gateway.app import (
    create_app_from_path as gateway_create_app_from_path,
)

create_app_from_config = gateway_create_app_from_config
create_app_from_path = gateway_create_app_from_path


def create_app_from_env() -> GatewayAPI:
    """
    Load the path from the environment variable and generate the GatewayAPI app instance.
    """
    if config_path := QCFLOW_DEPLOYMENTS_CONFIG.get():
        return create_app_from_path(config_path)

    raise QCFlowException(
        f"Environment variable {QCFLOW_DEPLOYMENTS_CONFIG!r} is not set. "
        "Please set it to the path of the gateway configuration file."
    )
