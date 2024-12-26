import filecmp
import logging
import os
import shutil

import pytest

from qcflow.entities import RunStatus
from qcflow.projects import _project_spec
from qcflow.utils.file_utils import TempDir, _copy_project

TEST_DIR = "tests"
TEST_PROJECT_DIR = os.path.abspath(os.path.join(TEST_DIR, "resources", "example_project"))
TEST_DOCKER_PROJECT_DIR = os.path.join(TEST_DIR, "resources", "example_docker_project")
TEST_VIRTUALENV_PROJECT_DIR = os.path.join(TEST_DIR, "resources", "example_virtualenv_project")
TEST_VIRTUALENV_CONDA_PROJECT_DIR = os.path.join(
    TEST_DIR, "resources", "example_virtualenv_conda_project"
)
TEST_VIRTUALENV_NO_PYTHON_ENV = os.path.join(
    TEST_DIR, "resources", "example_virtualenv_no_python_env"
)
TEST_PROJECT_NAME = "example_project"
TEST_NO_SPEC_PROJECT_DIR = os.path.join(TEST_DIR, "resources", "example_project_no_spec")
GIT_PROJECT_URI = "https://github.com/qcflow/qcflow-example"
GIT_PROJECT_BRANCH = "test-branch"
SSH_PROJECT_URI = "git@github.com:qcflow/qcflow-example.git"

_logger = logging.getLogger(__name__)


def load_project():
    """Loads an example project for use in tests, returning an in-memory `Project` object."""
    return _project_spec.load_project(TEST_PROJECT_DIR)


def validate_exit_status(status_str, expected):
    assert RunStatus.from_string(status_str) == expected


def assert_dirs_equal(expected, actual):
    dir_comparison = filecmp.dircmp(expected, actual)
    assert len(dir_comparison.left_only) == 0
    assert len(dir_comparison.right_only) == 0
    assert len(dir_comparison.diff_files) == 0
    assert len(dir_comparison.funny_files) == 0


@pytest.fixture(scope="package")
def docker_example_base_image():
    import docker
    from docker.errors import APIError, BuildError

    qcflow_home = os.environ.get("QCFLOW_HOME", None)
    if not qcflow_home:
        raise Exception(
            "QCFLOW_HOME environment variable is not set. Please set the variable to "
            "point to your qcflow dev root."
        )
    with TempDir() as tmp:
        cwd = tmp.path()
        qcflow_dir = _copy_project(src_path=qcflow_home, dst_path=cwd)
        shutil.copy(os.path.join(TEST_DOCKER_PROJECT_DIR, "Dockerfile"), tmp.path("Dockerfile"))
        with open(tmp.path("Dockerfile"), "a") as f:
            f.write(f"COPY {qcflow_dir} /opt/qcflow\nRUN pip install -U -e /opt/qcflow\n")

        client = docker.from_env()
        try:
            client.images.build(
                tag="qcflow-docker-example",
                forcerm=True,
                nocache=True,
                dockerfile="Dockerfile",
                path=cwd,
            )
        except BuildError as build_error:
            for chunk in build_error.build_log:
                _logger.info(chunk)
            raise build_error
        except APIError as api_error:
            raise api_error
