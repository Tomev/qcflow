import json
import os

import datasets
import pandas as pd
import pytest

import qcflow.data
import qcflow.data.huggingface_dataset
from qcflow.data.code_dataset_source import CodeDatasetSource
from qcflow.data.dataset_source_registry import get_dataset_source_from_json
from qcflow.data.evaluation_dataset import EvaluationDataset
from qcflow.data.huggingface_dataset import HuggingFaceDataset
from qcflow.data.huggingface_dataset_source import HuggingFaceDatasetSource
from qcflow.exceptions import MlflowException
from qcflow.types.schema import Schema
from qcflow.types.utils import _infer_schema


def test_from_huggingface_dataset_constructs_expected_dataset():
    ds = datasets.load_dataset("rotten_tomatoes", split="train")
    qcflow_ds = qcflow.data.from_huggingface(ds, path="rotten_tomatoes")

    assert isinstance(qcflow_ds, HuggingFaceDataset)
    assert qcflow_ds.ds == ds
    assert qcflow_ds.schema == _infer_schema(ds.to_pandas())
    assert qcflow_ds.profile == {
        "num_rows": ds.num_rows,
        "dataset_size": ds.dataset_size,
        "size_in_bytes": ds.size_in_bytes,
    }

    assert isinstance(qcflow_ds.source, HuggingFaceDatasetSource)

    with pytest.raises(KeyError, match="Found duplicated arguments*"):
        # Test that we raise an error if the same key is specified in both
        # `HuggingFaceDatasetSource` and `kwargs`.
        qcflow_ds.source.load(path="dummy_path")

    reloaded_ds = qcflow_ds.source.load()
    assert reloaded_ds.builder_name == ds.builder_name
    assert reloaded_ds.config_name == ds.config_name
    assert reloaded_ds.split == ds.split == "train"
    assert reloaded_ds.num_rows == ds.num_rows

    reloaded_qcflow_ds = qcflow.data.from_huggingface(reloaded_ds, path="rotten_tomatoes")
    assert reloaded_qcflow_ds.digest == qcflow_ds.digest


def test_from_huggingface_dataset_constructs_expected_dataset_with_revision():
    # Load this revision:
    # https://huggingface.co/datasets/cornell-movie-review-data/rotten_tomatoes/commit/aa13bc287fa6fcab6daf52f0dfb9994269ffea28
    revision = "aa13bc287fa6fcab6daf52f0dfb9994269ffea28"
    ds = datasets.load_dataset(
        "cornell-movie-review-data/rotten_tomatoes",
        split="train",
        revision=revision,
        trust_remote_code=True,
    )

    qcflow_ds_new = qcflow.data.from_huggingface(
        ds, path="rotten_tomatoes", revision=revision, trust_remote_code=True
    )

    ds = qcflow_ds_new.source.load()
    assert any(revision in cs for cs in ds.info.download_checksums)


def test_from_huggingface_dataset_constructs_expected_dataset_with_data_files():
    data_files = {"train": "prompts.csv"}
    ds = datasets.load_dataset("fka/awesome-chatgpt-prompts", data_files=data_files, split="train")
    qcflow_ds = qcflow.data.from_huggingface(
        ds, path="fka/awesome-chatgpt-prompts", data_files=data_files
    )

    assert isinstance(qcflow_ds, HuggingFaceDataset)
    assert qcflow_ds.ds == ds
    assert qcflow_ds.schema == _infer_schema(ds.to_pandas())
    assert qcflow_ds.profile == {
        "num_rows": ds.num_rows,
        "dataset_size": ds.dataset_size,
        "size_in_bytes": ds.size_in_bytes,
    }

    assert isinstance(qcflow_ds.source, HuggingFaceDatasetSource)
    reloaded_ds = qcflow_ds.source.load()
    assert reloaded_ds.builder_name == ds.builder_name
    assert reloaded_ds.config_name == ds.config_name
    assert reloaded_ds.split == ds.split == "train"
    assert reloaded_ds.num_rows == ds.num_rows

    reloaded_qcflow_ds = qcflow.data.from_huggingface(
        reloaded_ds, path="fka/awesome-chatgpt-prompts", data_files=data_files
    )
    assert reloaded_qcflow_ds.digest == qcflow_ds.digest


def test_from_huggingface_dataset_constructs_expected_dataset_with_data_dir(tmp_path):
    df = pd.DataFrame.from_dict({"a": [1, 2, 3], "b": [4, 5, 6]})
    data_dir = "data"
    os.makedirs(tmp_path / data_dir)
    df.to_csv(tmp_path / data_dir / "my_data.csv")
    ds = datasets.load_dataset(str(tmp_path), data_dir=data_dir, name="default", split="train")
    qcflow_ds = qcflow.data.from_huggingface(ds, path=str(tmp_path), data_dir=data_dir)

    assert qcflow_ds.ds == ds
    assert qcflow_ds.schema == _infer_schema(ds.to_pandas())
    assert qcflow_ds.profile == {
        "num_rows": ds.num_rows,
        "dataset_size": ds.dataset_size,
        "size_in_bytes": ds.size_in_bytes,
    }

    assert isinstance(qcflow_ds.source, HuggingFaceDatasetSource)
    reloaded_ds = qcflow_ds.source.load()
    assert reloaded_ds.builder_name == ds.builder_name
    assert reloaded_ds.config_name == ds.config_name
    assert reloaded_ds.split == ds.split == "train"
    assert reloaded_ds.num_rows == ds.num_rows

    reloaded_qcflow_ds = qcflow.data.from_huggingface(
        reloaded_ds, path=str(tmp_path), data_dir=data_dir
    )
    assert reloaded_qcflow_ds.digest == qcflow_ds.digest


def test_from_huggingface_dataset_respects_user_specified_name_and_digest():
    ds = datasets.load_dataset("rotten_tomatoes", split="train")
    qcflow_ds = qcflow.data.from_huggingface(
        ds, path="rotten_tomatoes", name="myname", digest="mydigest"
    )
    assert qcflow_ds.name == "myname"
    assert qcflow_ds.digest == "mydigest"


def test_from_huggingface_dataset_digest_is_consistent_for_large_ordered_datasets(tmp_path):
    assert (
        qcflow.data.huggingface_dataset._MAX_ROWS_FOR_DIGEST_COMPUTATION_AND_SCHEMA_INFERENCE
        < 200000
    )

    df = pd.DataFrame.from_dict(
        {
            "a": list(range(200000)),
            "b": list(range(200000)),
        }
    )
    data_dir = "data"
    os.makedirs(tmp_path / data_dir)
    df.to_csv(tmp_path / data_dir / "my_data.csv")

    ds = datasets.load_dataset(str(tmp_path), data_dir=data_dir, name="default", split="train")
    qcflow_ds = qcflow.data.from_huggingface(ds, path=str(tmp_path), data_dir=data_dir)
    assert qcflow_ds.digest == "1dda4ce8"


def test_from_huggingface_dataset_throws_for_dataset_dict():
    ds = datasets.load_dataset("rotten_tomatoes")
    assert isinstance(ds, datasets.DatasetDict)

    with pytest.raises(
        MlflowException, match="must be an instance of `datasets.Dataset`.*DatasetDict"
    ):
        qcflow.data.from_huggingface(ds, path="rotten_tomatoes")


def test_from_huggingface_dataset_no_source_specified():
    ds = datasets.load_dataset("rotten_tomatoes", split="train")
    qcflow_ds = qcflow.data.from_huggingface(ds)

    assert isinstance(qcflow_ds, HuggingFaceDataset)

    assert isinstance(qcflow_ds.source, CodeDatasetSource)
    assert "qcflow.source.name" in qcflow_ds.source.to_json()


def test_dataset_conversion_to_json():
    ds = datasets.load_dataset("rotten_tomatoes", split="train")
    qcflow_ds = qcflow.data.from_huggingface(ds, path="rotten_tomatoes")

    dataset_json = qcflow_ds.to_json()
    parsed_json = json.loads(dataset_json)
    assert parsed_json.keys() <= {"name", "digest", "source", "source_type", "schema", "profile"}
    assert parsed_json["name"] == qcflow_ds.name
    assert parsed_json["digest"] == qcflow_ds.digest
    assert parsed_json["source"] == qcflow_ds.source.to_json()
    assert parsed_json["source_type"] == qcflow_ds.source._get_source_type()
    assert parsed_json["profile"] == json.dumps(qcflow_ds.profile)

    schema_json = json.dumps(json.loads(parsed_json["schema"])["qcflow_colspec"])
    assert Schema.from_json(schema_json) == qcflow_ds.schema


def test_dataset_source_conversion_to_json():
    ds = datasets.load_dataset(
        "rotten_tomatoes",
        split="train",
        revision="c33cbf965006dba64f134f7bef69c53d5d0d285d",
    )
    qcflow_ds = qcflow.data.from_huggingface(
        ds,
        path="rotten_tomatoes",
        revision="c33cbf965006dba64f134f7bef69c53d5d0d285d",
    )
    source = qcflow_ds.source

    source_json = source.to_json()
    parsed_source = json.loads(source_json)
    assert parsed_source["revision"] == "c33cbf965006dba64f134f7bef69c53d5d0d285d"
    assert parsed_source["split"] == "train"
    assert parsed_source["config_name"] == "default"
    assert parsed_source["path"] == "rotten_tomatoes"
    assert not parsed_source["data_dir"]
    assert not parsed_source["data_files"]

    reloaded_source = HuggingFaceDatasetSource.from_json(source_json)
    assert json.loads(reloaded_source.to_json()) == parsed_source

    reloaded_source = get_dataset_source_from_json(
        source_json, source_type=source._get_source_type()
    )
    assert isinstance(reloaded_source, HuggingFaceDatasetSource)
    assert type(source) == type(reloaded_source)
    assert reloaded_source.to_json() == source.to_json()


def test_to_evaluation_dataset():
    import numpy as np

    ds = datasets.load_dataset("rotten_tomatoes", split="train")
    dataset = qcflow.data.from_huggingface(ds, path="rotten_tomatoes", targets="label")

    evaluation_dataset = dataset.to_evaluation_dataset()
    assert isinstance(evaluation_dataset, EvaluationDataset)
    assert evaluation_dataset.features_data.equals(dataset.ds.to_pandas().drop("label", axis=1))
    assert np.array_equal(evaluation_dataset.labels_data, dataset.ds.to_pandas()["label"].values)
