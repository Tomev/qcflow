from qcflow.environment_variables import (
    QCFLOW_ENABLE_ASYNC_LOGGING,
)
from qcflow.system_metrics import (
    disable_system_metrics_logging,
    enable_system_metrics_logging,
    set_system_metrics_node_id,
    set_system_metrics_samples_before_logging,
    set_system_metrics_sampling_interval,
)
from qcflow.tracking import (
    get_registry_uri,
    get_tracking_uri,
    is_tracking_uri_set,
    set_registry_uri,
    set_tracking_uri,
)


def enable_async_logging(enable=True):
    """Enable or disable async logging globally.

    Args:
        enable: bool, if True, enable async logging. If False, disable async logging.

    .. code-block:: python
        :caption: Example

        import qcflow

        qcflow.config.enable_async_logging(True)

        with qcflow.start_run():
            qcflow.log_param("a", 1)  # This will be logged asynchronously

        qcflow.config.enable_async_logging(False)
        with qcflow.start_run():
            qcflow.log_param("a", 1)  # This will be logged synchronously
    """

    QCFLOW_ENABLE_ASYNC_LOGGING.set(enable)


__all__ = [
    "enable_system_metrics_logging",
    "disable_system_metrics_logging",
    "enable_async_logging",
    "get_registry_uri",
    "get_tracking_uri",
    "is_tracking_uri_set",
    "set_registry_uri",
    "set_system_metrics_sampling_interval",
    "set_system_metrics_samples_before_logging",
    "set_system_metrics_node_id",
    "set_tracking_uri",
]
