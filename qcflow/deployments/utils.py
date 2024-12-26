import urllib
from typing import Optional
from urllib.parse import urlparse

from qcflow.environment_variables import QCFLOW_DEPLOYMENTS_TARGET
from qcflow.exceptions import MlflowException
from qcflow.utils.uri import append_to_uri_path

_deployments_target: Optional[str] = None


def parse_target_uri(target_uri):
    """Parse out the deployment target from the provided target uri"""
    parsed = urllib.parse.urlparse(target_uri)
    if not parsed.scheme:
        if parsed.path:
            # uri = 'target_name' (without :/<path>)
            return parsed.path
        raise MlflowException(
            f"Not a proper deployment URI: {target_uri}. "
            + "Deployment URIs must be of the form 'target' or 'target:/suffix'"
        )
    return parsed.scheme


def _is_valid_uri(uri: str) -> bool:
    """
    Evaluates the basic structure of a provided uri to determine if the scheme and
    netloc are provided
    """
    try:
        parsed = urlparse(uri)
        return bool(parsed.scheme and parsed.netloc)
    except ValueError:
        return False


def resolve_endpoint_url(base_url: str, endpoint: str) -> str:
    """Performs a validation on whether the returned value is a fully qualified url
    or requires the assembly of a fully qualified url by appending `endpoint`.

    Args:
        base_url: The base URL. Should include the scheme and domain, e.g.,
            ``http://127.0.0.1:6000``.
        endpoint: The endpoint to be appended to the base URL, e.g., ``/api/2.0/endpoints/`` or,
            in the case of Databricks, the fully qualified url.

    Returns:
        The complete URL, either directly returned or formed and returned by joining the
        base URL and the endpoint path.

    """
    return endpoint if _is_valid_uri(endpoint) else append_to_uri_path(base_url, endpoint)


def set_deployments_target(target: str):
    """Sets the target deployment client for QCFlow deployments

    Args:
        target: The full uri of a running QCFlow AI Gateway or, if running on
            Databricks, "databricks".
    """
    if not _is_valid_target(target):
        raise MlflowException.invalid_parameter_value(
            "The target provided is not a valid uri or 'databricks'"
        )

    global _deployments_target
    _deployments_target = target


def get_deployments_target() -> str:
    """
    Returns the currently set QCFlow deployments target iff set.
    If the deployments target has not been set by using ``set_deployments_target``, an
    ``MlflowException`` is raised.
    """
    if _deployments_target is not None:
        return _deployments_target
    elif uri := QCFLOW_DEPLOYMENTS_TARGET.get():
        return uri
    else:
        raise MlflowException(
            "No deployments target has been set. Please either set the QCFlow deployments target"
            " via `qcflow.deployments.set_deployments_target()` or set the environment variable "
            f"{QCFLOW_DEPLOYMENTS_TARGET} to the running deployment server's uri"
        )


def _is_valid_target(target: str):
    """
    Evaluates the basic structure of a provided target to determine if the scheme and
    netloc are provided
    """
    if target == "databricks":
        return True
    return _is_valid_uri(target)
