import click

from qcflow.environment_variables import QCFLOW_GATEWAY_CONFIG
from qcflow.gateway.config import _validate_config
from qcflow.gateway.runner import run_app
from qcflow.utils.os import is_windows


def validate_config_path(_ctx, _param, value):
    try:
        _validate_config(value)
        return value
    except Exception as e:
        raise click.BadParameter(str(e))


@click.group("gateway", help="Manage the QCFlow Gateway service")
def commands():
    pass


@commands.command("start", help="Start the QCFlow Gateway service")
@click.option(
    "--config-path",
    envvar=QCFLOW_GATEWAY_CONFIG.name,
    callback=validate_config_path,
    required=True,
    help="The path to the gateway configuration file.",
)
@click.option(
    "--host",
    default="127.0.0.1",
    help="The network address to listen on (default: 127.0.0.1).",
)
@click.option(
    "--port",
    default=5000,
    help="The port to listen on (default: 5000).",
)
@click.option(
    "--workers",
    default=2,
    help="The number of workers.",
)
def start(config_path: str, host: str, port: str, workers: int):
    if is_windows():
        raise click.ClickException("QCFlow AI Gateway does not support Windows.")
    run_app(config_path=config_path, host=host, port=port, workers=workers)
