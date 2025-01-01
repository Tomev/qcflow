import logging

from qcflow.projects.backend.local import LocalBackend
from qcflow.utils.plugins import get_entry_points

ENTRYPOINT_GROUP_NAME = "qcflow.project_backend"

_logger = logging.getLogger(__name__)


# Statically register backend defined in qcflow
QCFLOW_BACKENDS = {
    "local": LocalBackend,
}


def load_backend(backend_name):
    # Static backends
    if backend_name in QCFLOW_BACKENDS:
        return QCFLOW_BACKENDS[backend_name]()

    # backends from plugin
    entrypoints = get_entry_points(ENTRYPOINT_GROUP_NAME)
    if entrypoint := next((e for e in entrypoints if e.name == backend_name), None):
        builder = entrypoint.load()
        return builder()

    # TODO Should be a error when all backends are migrated here
    _logger.warning(
        "Backend '%s' is not available. Available plugins are %s",
        backend_name,
        [*entrypoints, *QCFLOW_BACKENDS.keys()],
    )

    return None
