import os
from unittest import mock

import pytest

import docker
import qcflow
from qcflow import QCFlowClient
from qcflow.entities import ViewType
from qcflow.environment_variables import QCFLOW_TRACKING_URI
from qcflow.exceptions import QCFlowException
from qcflow.legacy_databricks_cli.configure.provider import DatabricksConfig
from qcflow.projects import ExecutionException, _project_spec
from qcflow.projects.backend.local import _get_docker_command
from qcflow.projects.docker import _get_docker_image_uri
from qcflow.store.tracking import file_store
from qcflow.utils.qcflow_tags import (
    QCFLOW_DOCKER_IMAGE_ID,
    QCFLOW_DOCKER_IMAGE_URI,
    QCFLOW_PROJECT_BACKEND,
    QCFLOW_PROJECT_ENV,
)

from tests.projects.utils import (
    TEST_DOCKER_PROJECT_DIR,
    docker_example_base_image,  # noqa: F401
)


def _build_uri(base_uri, subdirectory):
    if subdirectory != "":
        return f"{base_uri}#{subdirectory}"
    return base_uri


@pytest.mark.parametrize("use_start_run", map(str, [0, 1]))
def test_docker_project_execution(use_start_run, docker_example_base_image):
    expected_params = {"use_start_run": use_start_run}
    submitted_run = qcflow.projects.run(
        TEST_DOCKER_PROJECT_DIR,
        experiment_id=file_store.FileStore.DEFAULT_EXPERIMENT_ID,
        parameters=expected_params,
        entry_point="test_tracking",
        build_image=True,
        docker_args={"memory": "1g", "privileged": True},
    )
    # Validate run contents in the FileStore
    run_id = submitted_run.run_id
    qcflow_service = QCFlowClient()
    runs = qcflow_service.search_runs(
        [file_store.FileStore.DEFAULT_EXPERIMENT_ID], run_view_type=ViewType.ACTIVE_ONLY
    )
    assert len(runs) == 1
    store_run_id = runs[0].info.run_id
    assert run_id == store_run_id
    run = qcflow_service.get_run(run_id)
    assert run.data.params == expected_params
    assert run.data.metrics == {"some_key": 3}
    exact_expected_tags = {
        QCFLOW_PROJECT_ENV: "docker",
        QCFLOW_PROJECT_BACKEND: "local",
    }
    approx_expected_tags = {
        QCFLOW_DOCKER_IMAGE_URI: "docker-example",
        QCFLOW_DOCKER_IMAGE_ID: "sha256:",
    }
    run_tags = run.data.tags
    for k, v in exact_expected_tags.items():
        assert run_tags[k] == v
    for k, v in approx_expected_tags.items():
        assert run_tags[k].startswith(v)
    artifacts = qcflow_service.list_artifacts(run_id=run_id)
    assert len(artifacts) == 1
    docker_cmd = submitted_run.command_proc.args[2]
    assert "--memory 1g" in docker_cmd
    assert "--privileged" in docker_cmd


def test_docker_project_execution_async_docker_args(
    docker_example_base_image,
):
    submitted_run = qcflow.projects.run(
        TEST_DOCKER_PROJECT_DIR,
        experiment_id=file_store.FileStore.DEFAULT_EXPERIMENT_ID,
        parameters={"use_start_run": "0"},
        entry_point="test_tracking",
        docker_args={"memory": "1g", "privileged": True},
        synchronous=False,
    )
    submitted_run.wait()

    args = submitted_run.command_proc.args
    assert len([a for a in args if a == "--docker-args"]) == 2
    first_idx = args.index("--docker-args")
    second_idx = args.index("--docker-args", first_idx + 1)
    assert args[first_idx + 1] == "memory=1g"
    assert args[second_idx + 1] == "privileged"


@pytest.mark.parametrize(
    ("tracking_uri", "expected_command_segment"),
    [
        (None, "-e QCFLOW_TRACKING_URI=/qcflow/tmp/mlruns"),
        ("http://some-tracking-uri", "-e QCFLOW_TRACKING_URI=http://some-tracking-uri"),
        ("databricks://some-profile", "-e QCFLOW_TRACKING_URI=databricks "),
    ],
)
@mock.patch("qcflow.utils.databricks_utils.ProfileConfigProvider")
def test_docker_project_tracking_uri_propagation(
    ProfileConfigProvider,
    tmp_path,
    tracking_uri,
    expected_command_segment,
    docker_example_base_image,
):
    mock_provider = mock.MagicMock()
    mock_provider.get_config.return_value = DatabricksConfig.from_password(
        "host", "user", "pass", insecure=True
    )
    ProfileConfigProvider.return_value = mock_provider
    # Create and mock local tracking directory
    local_tracking_dir = os.path.join(tmp_path, "mlruns")
    if tracking_uri is None:
        tracking_uri = local_tracking_dir
    old_uri = qcflow.get_tracking_uri()
    try:
        qcflow.set_tracking_uri(tracking_uri)
        with mock.patch(
            "qcflow.tracking._tracking_service.utils._get_store",
            return_value=file_store.FileStore(local_tracking_dir),
        ):
            qcflow.projects.run(
                TEST_DOCKER_PROJECT_DIR, experiment_id=file_store.FileStore.DEFAULT_EXPERIMENT_ID
            )
    finally:
        qcflow.set_tracking_uri(old_uri)


def test_docker_uri_mode_validation(docker_example_base_image):
    with pytest.raises(ExecutionException, match="When running on Databricks"):
        qcflow.projects.run(TEST_DOCKER_PROJECT_DIR, backend="databricks", backend_config={})


@mock.patch("qcflow.projects.docker.get_git_commit")
def test_docker_image_uri_with_git(get_git_commit_mock):
    get_git_commit_mock.return_value = "1234567890"
    image_uri = _get_docker_image_uri("my_project", "my_workdir")
    assert image_uri == "my_project:1234567"
    get_git_commit_mock.assert_called_with("my_workdir")


@mock.patch("qcflow.projects.docker.get_git_commit")
def test_docker_image_uri_no_git(get_git_commit_mock):
    get_git_commit_mock.return_value = None
    image_uri = _get_docker_image_uri("my_project", "my_workdir")
    assert image_uri == "my_project"
    get_git_commit_mock.assert_called_with("my_workdir")


def test_docker_valid_project_backend_local():
    work_dir = "./examples/docker"
    project = _project_spec.load_project(work_dir)
    qcflow.projects.docker.validate_docker_env(project)


def test_docker_invalid_project_backend_local():
    work_dir = "./examples/docker"
    project = _project_spec.load_project(work_dir)
    project.name = None
    with pytest.raises(ExecutionException, match="Project name in MLProject must be specified"):
        qcflow.projects.docker.validate_docker_env(project)


@pytest.mark.parametrize(
    ("artifact_uri", "host_artifact_uri", "container_artifact_uri", "should_mount"),
    [
        ("/tmp/mlruns/artifacts", "/tmp/mlruns/artifacts", "/tmp/mlruns/artifacts", True),
        ("s3://my_bucket", None, None, False),
        ("file:///tmp/mlruns/artifacts", "/tmp/mlruns/artifacts", "/tmp/mlruns/artifacts", True),
        ("./mlruns", os.path.abspath("./mlruns"), "/qcflow/projects/code/mlruns", True),
    ],
)
def test_docker_mount_local_artifact_uri(
    artifact_uri, host_artifact_uri, container_artifact_uri, should_mount
):
    active_run = mock.MagicMock()
    run_info = mock.MagicMock()
    run_info.run_id = "fake_run_id"
    run_info.experiment_id = "fake_experiment_id"
    run_info.artifact_uri = artifact_uri
    active_run.info = run_info
    image = mock.MagicMock()
    image.tags = ["image:tag"]

    docker_command = _get_docker_command(image, active_run)

    docker_volume_expected = f"-v {host_artifact_uri}:{container_artifact_uri}"
    assert (docker_volume_expected in " ".join(docker_command)) == should_mount


@mock.patch("qcflow.utils.databricks_utils.ProfileConfigProvider")
def test_docker_databricks_tracking_cmd_and_envs(ProfileConfigProvider):
    mock_provider = mock.MagicMock()
    mock_provider.get_config.return_value = DatabricksConfig.from_password(
        "host", "user", "pass", insecure=True
    )
    ProfileConfigProvider.return_value = mock_provider

    cmds, envs = qcflow.projects.docker.get_docker_tracking_cmd_and_envs(
        "databricks://some-profile"
    )
    assert envs == {
        "DATABRICKS_HOST": "host",
        "DATABRICKS_USERNAME": "user",
        "DATABRICKS_PASSWORD": "pass",
        "DATABRICKS_INSECURE": "True",
        QCFLOW_TRACKING_URI.name: "databricks",
    }
    assert cmds == []


@pytest.mark.parametrize(
    ("volumes", "environment", "os_environ", "expected"),
    [
        ([], ["VAR1"], {"VAR1": "value1"}, [("-e", "VAR1=value1")]),
        ([], ["VAR1"], {}, ["should_crash", ("-e", "VAR1=value1")]),
        ([], ["VAR1"], {"OTHER_VAR": "value1"}, ["should_crash", ("-e", "VAR1=value1")]),
        (
            [],
            ["VAR1", ["VAR2", "value2"]],
            {"VAR1": "value1"},
            [("-e", "VAR1=value1"), ("-e", "VAR2=value2")],
        ),
        ([], [["VAR2", "value2"]], {"VAR1": "value1"}, [("-e", "VAR2=value2")]),
        (
            ["/path:/path"],
            ["VAR1"],
            {"VAR1": "value1"},
            [("-e", "VAR1=value1"), ("-v", "/path:/path")],
        ),
        (
            ["/path:/path"],
            [["VAR2", "value2"]],
            {"VAR1": "value1"},
            [("-e", "VAR2=value2"), ("-v", "/path:/path")],
        ),
    ],
)
def test_docker_user_specified_env_vars(volumes, environment, expected, os_environ, monkeypatch):
    active_run = mock.MagicMock()
    run_info = mock.MagicMock()
    run_info.run_id = "fake_run_id"
    run_info.experiment_id = "fake_experiment_id"
    run_info.artifact_uri = "/tmp/mlruns/artifacts"
    active_run.info = run_info
    image = mock.MagicMock()
    image.tags = ["image:tag"]

    monkeypatch.setenvs(os_environ)
    if "should_crash" in expected:
        expected.remove("should_crash")
        with pytest.raises(QCFlowException, match="This project expects"):
            _get_docker_command(image, active_run, None, volumes, environment)
    else:
        docker_command = _get_docker_command(image, active_run, None, volumes, environment)
        for exp_type, expected in expected:
            assert expected in docker_command
            assert docker_command[docker_command.index(expected) - 1] == exp_type


@pytest.mark.parametrize("docker_args", [{}, {"ARG": "VAL"}, {"ARG1": "VAL1", "ARG2": "VAL2"}])
def test_docker_run_args(docker_args):
    active_run = mock.MagicMock()
    run_info = mock.MagicMock()
    run_info.run_id = "fake_run_id"
    run_info.experiment_id = "fake_experiment_id"
    run_info.artifact_uri = "/tmp/mlruns/artifacts"
    active_run.info = run_info
    image = mock.MagicMock()
    image.tags = ["image:tag"]

    docker_command = _get_docker_command(image, active_run, docker_args, None, None)

    for flag, value in docker_args.items():
        assert docker_command[docker_command.index(value) - 1] == f"--{flag}"


def test_docker_build_image_local(tmp_path):
    client = docker.from_env()
    dockerfile = tmp_path.joinpath("Dockerfile")
    dockerfile.write_text(
        """
FROM python:3.9
RUN pip --version
"""
    )
    client.images.build(path=str(tmp_path), dockerfile=str(dockerfile), tag="my-python:latest")
    tmp_path.joinpath("MLproject").write_text(
        """
name: test
docker_env:
  image: my-python
entry_points:
  main:
    command: python --version
"""
    )
    submitted_run = qcflow.projects.run(str(tmp_path))
    run = qcflow.get_run(submitted_run.run_id)
    assert run.data.tags[QCFLOW_DOCKER_IMAGE_URI] == "my-python"


def test_docker_build_image_remote(tmp_path):
    tmp_path.joinpath("MLproject").write_text(
        """
name: test
docker_env:
  image: python:3.9
entry_points:
  main:
    command: python --version
"""
    )
    submitted_run = qcflow.projects.run(str(tmp_path))
    run = qcflow.get_run(submitted_run.run_id)
    assert run.data.tags[QCFLOW_DOCKER_IMAGE_URI] == "python:3.9"
