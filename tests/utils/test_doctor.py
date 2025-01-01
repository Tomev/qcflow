from unittest import mock

import qcflow


def test_doctor(capsys):
    qcflow.doctor()
    captured = capsys.readouterr()
    assert f"QCFlow version: {qcflow.__version__}" in captured.out


def test_doctor_active_run(capsys):
    with qcflow.start_run() as run:
        qcflow.doctor()
        captured = capsys.readouterr()
        assert f"Active run ID: {run.info.run_id}" in captured.out


def test_doctor_databricks_runtime(capsys):
    mock_version = "12.0"
    with mock.patch(
        "qcflow.utils.doctor.get_databricks_runtime_version", return_value=mock_version
    ) as mock_runtime:
        qcflow.doctor()
        mock_runtime.assert_called_once()
        captured = capsys.readouterr()
        assert f"Databricks runtime version: {mock_version}" in captured.out
