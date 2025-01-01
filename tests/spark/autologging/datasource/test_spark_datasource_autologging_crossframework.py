import time

import numpy as np
import pytest
from sklearn.linear_model import LinearRegression

import qcflow
import qcflow.spark

from tests.spark.autologging.utils import _assert_spark_data_logged


@pytest.fixture
def http_tracking_uri_mock():
    qcflow.set_tracking_uri("http://some-cool-uri")
    yield
    qcflow.set_tracking_uri(None)


def _fit_sklearn(pandas_df):
    x = pandas_df.values
    y = np.array([4] * len(x))
    LinearRegression().fit(x, y)
    # Sleep to allow time for datasource read event to fire asynchronously from the JVM & for
    # the Python-side event handler to run & log a tag to the current active run.
    # This race condition (& the risk of dropping datasource read events for short-lived runs)
    # is known and documented in
    # https://qcflow.org/docs/latest/python_api/qcflow.spark.html#qcflow.spark.autolog
    time.sleep(5)


def _fit_sklearn_model_with_active_run(pandas_df):
    run_id = qcflow.active_run().info.run_id
    _fit_sklearn(pandas_df)
    return qcflow.get_run(run_id)


def _fit_sklearn_model_no_active_run(pandas_df):
    orig_runs = qcflow.search_runs()
    orig_run_ids = set(orig_runs["run_id"])
    _fit_sklearn(pandas_df)
    new_runs = qcflow.search_runs()
    new_run_ids = set(new_runs["run_id"])
    assert len(new_run_ids) == len(orig_run_ids) + 1
    run_id = (new_run_ids - orig_run_ids).pop()
    return qcflow.get_run(run_id)


def _fit_sklearn_model(pandas_df):
    active_run = qcflow.active_run()
    if active_run:
        return _fit_sklearn_model_with_active_run(pandas_df)
    else:
        return _fit_sklearn_model_no_active_run(pandas_df)


def test_spark_autologging_with_sklearn_autologging(spark_session, data_format, file_path):
    assert qcflow.active_run() is None
    qcflow.spark.autolog()
    qcflow.sklearn.autolog()
    df = (
        spark_session.read.format(data_format)
        .option("header", "true")
        .option("inferSchema", "true")
        .load(file_path)
        .select("number1", "number2")
    )
    pandas_df = df.toPandas()
    run = _fit_sklearn_model(pandas_df)
    _assert_spark_data_logged(run, file_path, data_format)
    assert qcflow.active_run() is None


def test_spark_sklearn_autologging_context_provider(spark_session, data_format, file_path):
    qcflow.spark.autolog()
    qcflow.sklearn.autolog()

    df = (
        spark_session.read.format(data_format)
        .option("header", "true")
        .option("inferSchema", "true")
        .load(file_path)
        .select("number1", "number2")
    )
    pandas_df = df.toPandas()

    # DF info should be logged to the first run (it should be added to our context provider after
    # the toPandas() call above & then logged here)
    with qcflow.start_run():
        run = _fit_sklearn_model(pandas_df)
    _assert_spark_data_logged(run, file_path, data_format)

    with qcflow.start_run():
        pandas_df2 = df.filter("number1 > 0").toPandas()
        run2 = _fit_sklearn_model(pandas_df2)
    assert run2.info.run_id != run.info.run_id
    _assert_spark_data_logged(run2, file_path, data_format)
    time.sleep(1)
    assert qcflow.active_run() is None


def test_spark_and_sklearn_autologging_all_runs_managed(spark_session, data_format, file_path):
    qcflow.spark.autolog()
    qcflow.sklearn.autolog()
    for _ in range(2):
        with qcflow.start_run():
            df = (
                spark_session.read.format(data_format)
                .option("header", "true")
                .option("inferSchema", "true")
                .load(file_path)
                .select("number1", "number2")
            )
            pandas_df = df.toPandas()
            run = _fit_sklearn_model(pandas_df)
        _assert_spark_data_logged(run, file_path, data_format)
    assert qcflow.active_run() is None
