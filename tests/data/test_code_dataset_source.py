from qcflow.data.code_dataset_source import CodeDatasetSource


def test_code_dataset_source_from_path():
    tags = {
        "qcflow_source_type": "NOTEBOOK",
        "qcflow_source_name": "some_random_notebook_path",
    }
    code_datasource = CodeDatasetSource(tags)
    assert code_datasource.to_dict() == {
        "tags": tags,
    }


def test_code_datasource_type():
    assert CodeDatasetSource._get_source_type() == "code"
