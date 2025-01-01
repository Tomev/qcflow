# Import a dependency in QCFlow's setup.py that's in our conda.yaml but not included with QCFlow
# by default, verify that we can use it.

import os
import sys

import psutil

import qcflow


def main(expected_env_name):
    actual_conda_env = os.environ.get("CONDA_DEFAULT_ENV", None)
    assert actual_conda_env == expected_env_name, (
        f"Script expected to be run from conda env {expected_env_name} but was actually run "
        f" from env {actual_conda_env}"
    )
    qcflow.log_metric("CPU usage", psutil.cpu_percent())


if __name__ == "__main__":
    main(sys.argv[1])
