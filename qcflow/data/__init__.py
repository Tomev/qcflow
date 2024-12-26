import sys
from contextlib import suppress
from typing import Union

from qcflow.data import dataset_registry
from qcflow.data import sources as qcflow_data_sources
from qcflow.data.dataset import Dataset
from qcflow.data.dataset_source import DatasetSource
from qcflow.data.dataset_source_registry import get_dataset_source_from_json, get_registered_sources
from qcflow.entities import Dataset as DatasetEntity
from qcflow.entities import DatasetInput
from qcflow.exceptions import QCFlowException
from qcflow.protos.databricks_pb2 import INVALID_PARAMETER_VALUE

with suppress(ImportError):
    # Suppressing ImportError to pass qcflow-skinny testing.
    from qcflow.data import meta_dataset  # noqa: F401


def get_source(dataset: Union[DatasetEntity, DatasetInput, Dataset]) -> DatasetSource:
    """Obtains the source of the specified dataset or dataset input.

    Args:
        dataset:
            An instance of :py:class:`qcflow.data.dataset.Dataset <qcflow.data.dataset.Dataset>`,
            :py:class:`qcflow.entities.Dataset`, or :py:class:`qcflow.entities.DatasetInput`.

    Returns:
        An instance of :py:class:`DatasetSource <qcflow.data.dataset_source.DatasetSource>`.

    """
    if isinstance(dataset, DatasetInput):
        dataset: DatasetEntity = dataset.dataset

    if isinstance(dataset, DatasetEntity):
        dataset_source: DatasetSource = get_dataset_source_from_json(
            source_json=dataset.source,
            source_type=dataset.source_type,
        )
    elif isinstance(dataset, Dataset):
        dataset_source: DatasetSource = dataset.source
    else:
        raise QCFlowException(
            f"Unrecognized dataset type {type(dataset)}. Expected one of: "
            f"`qcflow.data.dataset.Dataset`,"
            f" `qcflow.entities.Dataset`, `qcflow.entities.DatasetInput`.",
            INVALID_PARAMETER_VALUE,
        )

    return dataset_source


__all__ = ["get_source"]


def _define_dataset_constructors_in_current_module():
    data_module = sys.modules[__name__]
    for (
        constructor_name,
        constructor_fn,
    ) in dataset_registry.get_registered_constructors().items():
        setattr(data_module, constructor_name, constructor_fn)
        __all__.append(constructor_name)


_define_dataset_constructors_in_current_module()


def _define_dataset_sources_in_sources_module():
    for source in get_registered_sources():
        setattr(qcflow_data_sources, source.__name__, source)
        qcflow_data_sources.__all__.append(source.__name__)


_define_dataset_sources_in_sources_module()
