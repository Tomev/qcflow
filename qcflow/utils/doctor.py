import os
import platform

import click
import importlib_metadata
import yaml
from packaging.requirements import Requirement

import qcflow
from qcflow.utils.databricks_utils import get_databricks_runtime_version


def doctor(mask_envs=False):
    """Prints out useful information for debugging issues with QCFlow.

    Args:
        mask_envs: If True, mask the QCFlow environment variable values
            (e.g. `"QCFLOW_ENV_VAR": "***"`) in the output to prevent leaking sensitive
            information.

    .. warning::

        - This API should only be used for debugging purposes.
        - The output may contain sensitive information such as a database URI containing a password.

    .. code-block:: python
        :caption: Example

        import qcflow

        with qcflow.start_run():
            qcflow.doctor()

    .. code-block:: text
        :caption: Output

        System information: Linux #58~20.04.1-Ubuntu SMP Thu Oct 13 13:09:46 UTC 2022
        Python version: 3.8.13
        QCFlow version: 2.0.1
        QCFlow module location: /usr/local/lib/python3.8/site-packages/qcflow/__init__.py
        Tracking URI: sqlite:///qcflow.db
        Registry URI: sqlite:///qcflow.db
        QCFlow environment variables:
          QCFLOW_TRACKING_URI: sqlite:///qcflow.db
        QCFlow dependencies:
          Flask: 2.2.2
          Jinja2: 3.0.3
          alembic: 1.8.1
          click: 8.1.3
          cloudpickle: 2.2.0
          databricks-cli: 0.17.4.dev0
          docker: 6.0.0
          entrypoints: 0.4
          gitpython: 3.1.29
          gunicorn: 20.1.0
          importlib-metadata: 5.0.0
          markdown: 3.4.1
          matplotlib: 3.6.1
          numpy: 1.23.4
          packaging: 21.3
          pandas: 1.5.1
          protobuf: 3.19.6
          pyarrow: 9.0.0
          pytz: 2022.6
          pyyaml: 6.0
          querystring-parser: 1.2.4
          requests: 2.28.1
          scikit-learn: 1.1.3
          scipy: 1.9.3
          shap: 0.41.0
          sqlalchemy: 1.4.42
          sqlparse: 0.4.3
    """
    items = [
        ("System information", " ".join((platform.system(), platform.version()))),
        ("Python version", platform.python_version()),
        ("QCFlow version", qcflow.__version__),
        ("QCFlow module location", qcflow.__file__),
        ("Tracking URI", qcflow.get_tracking_uri()),
        ("Registry URI", qcflow.get_registry_uri()),
    ]

    if (runtime := get_databricks_runtime_version()) is not None:
        items.append(("Databricks runtime version", runtime))

    active_run = qcflow.active_run()
    if active_run:
        items.extend(
            [
                ("Active experiment ID", active_run.info.experiment_id),
                ("Active run ID", active_run.info.run_id),
                ("Active run artifact URI", active_run.info.artifact_uri),
            ]
        )

    qcflow_envs = {
        k: ("***" if mask_envs else v) for k, v in os.environ.items() if k.startswith("QCFLOW_")
    }
    if qcflow_envs:
        items.append(
            (
                "QCFlow environment variables",
                yaml.dump({"_": qcflow_envs}, indent=2).replace("'", "").lstrip("_:").rstrip("\n"),
            )
        )

    qcflow_dependencies = {}
    for req in importlib_metadata.requires("qcflow"):
        req = Requirement(req)
        try:
            dist = importlib_metadata.distribution(req.name)
        except importlib_metadata.PackageNotFoundError:
            continue
        else:
            qcflow_dependencies[req.name] = dist.version

    items.append(
        (
            "QCFlow dependencies",
            yaml.dump({"_": qcflow_dependencies}, indent=2)
            .replace("'", "")
            .lstrip("_:")
            .rstrip("\n"),
        )
    )
    for key, val in items:
        click.secho(key, fg="blue", nl=False)
        click.echo(f": {val}")
