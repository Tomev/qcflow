from flask import request
from prometheus_flask_exporter.multiprocess import GunicornInternalPrometheusMetrics

from qcflow.version import VERSION


def activate_prometheus_exporter(app):
    def qcflow_version(_: request):
        return VERSION

    return GunicornInternalPrometheusMetrics(
        app,
        export_defaults=True,
        defaults_prefix="qcflow",
        excluded_paths=["/health", "/version"],
        group_by=qcflow_version,
    )
