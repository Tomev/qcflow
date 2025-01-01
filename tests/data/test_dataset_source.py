import json

import pandas as pd
import pytest

import qcflow.data
from qcflow.exceptions import QCFlowException

from tests.resources.data.dataset_source import SampleDatasetSource


def test_load(tmp_path):
    assert SampleDatasetSource("test:" + str(tmp_path)).load() == str(tmp_path)


def test_conversion_to_json_and_back():
    uri = "test:/my/test/uri"
    source = SampleDatasetSource._resolve(uri)
    source_json = source.to_json()
    assert json.loads(source_json)["uri"] == uri
    reloaded_source = SampleDatasetSource.from_json(source_json)
    assert reloaded_source.uri == source.uri


def test_get_source_obtains_expected_file_source(tmp_path):
    df = pd.DataFrame([[1, 2, 3], [1, 2, 3]], columns=["a", "b", "c"])
    path = tmp_path / "temp.csv"
    df.to_csv(path)
    pandas_ds = qcflow.data.from_pandas(df, source=path)

    source1 = qcflow.data.get_source(pandas_ds)
    assert json.loads(source1.to_json()) == json.loads(pandas_ds.source.to_json())

    with qcflow.start_run() as r:
        qcflow.log_input(pandas_ds)

    run = qcflow.get_run(r.info.run_id)

    ds_input = run.inputs.dataset_inputs[0]
    source2 = qcflow.data.get_source(ds_input)
    assert json.loads(source2.to_json()) == json.loads(pandas_ds.source.to_json())

    ds_entity = run.inputs.dataset_inputs[0].dataset
    source3 = qcflow.data.get_source(ds_entity)
    assert json.loads(source3.to_json()) == json.loads(pandas_ds.source.to_json())

    assert source1.load() == source2.load() == source3.load() == str(path)


def test_get_source_obtains_expected_code_source():
    df = pd.DataFrame([[1, 2, 3], [1, 2, 3]], columns=["a", "b", "c"])
    pandas_ds = qcflow.data.from_pandas(df)

    source1 = qcflow.data.get_source(pandas_ds)
    assert json.loads(source1.to_json()) == json.loads(pandas_ds.source.to_json())

    with qcflow.start_run() as r:
        qcflow.log_input(pandas_ds)

    run = qcflow.get_run(r.info.run_id)

    ds_input = run.inputs.dataset_inputs[0]
    source2 = qcflow.data.get_source(ds_input)
    assert json.loads(source2.to_json()) == json.loads(pandas_ds.source.to_json())

    ds_entity = run.inputs.dataset_inputs[0].dataset
    source3 = qcflow.data.get_source(ds_entity)
    assert json.loads(source3.to_json()) == json.loads(pandas_ds.source.to_json())


def test_get_source_throws_for_invalid_input(tmp_path):
    with pytest.raises(QCFlowException, match="Unrecognized dataset type.*str"):
        qcflow.data.get_source(str(tmp_path))
