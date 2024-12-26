import logging
from typing import Any

from qcflow.data.dataset_source import DatasetSource
from qcflow.exceptions import QCFlowException

_logger = logging.getLogger(__name__)


class UCVolumeDatasetSource(DatasetSource):
    """Represents the source of a dataset stored in Databricks Unified Catalog Volume.

    If you are using a delta table, please use `qcflow.data.delta_dataset_source.DeltaDatasetSource`
    instead. This `UCVolumeDatasetSource` does not provide loading function, and is mostly useful
    when you are logging a `qcflow.data.meta_dataset.MetaDataset` to QCFlow, i.e., you want
    to log the source of dataset to QCFlow without loading the dataset.

    Args:
        path: the UC path of your data. It should be a valid UC path following the pattern
            "/Volumes/{catalog}/{schema}/{volume}/{file_path}". For example,
            "/Volumes/MyCatalog/MySchema/MyVolume/MyFile.json".
    """

    def __init__(self, path: str):
        self.path = path
        self._verify_uc_path_is_valid()

    def _verify_uc_path_is_valid(self):
        """Verify if the path exists in Databricks Unified Catalog."""
        try:
            from databricks.sdk import WorkspaceClient

            w = WorkspaceClient()
        except ImportError:
            _logger.warning(
                "Cannot verify the path of `UCVolumeDatasetSource` because of missing"
                "`databricks-sdk`. Please install `databricks-sdk` via "
                "`pip install -U databricks-sdk`. This does not block creating "
                "`UCVolumeDatasetSource`, but your `UCVolumeDatasetSource` might be invalid."
            )
            return
        except Exception:
            _logger.warning(
                "Cannot verify the path of `UCVolumeDatasetSource` due to a connection failure "
                "with Databricks workspace. Please run `qcflow.login()` to log in to Databricks. "
                "This does not block creating `UCVolumeDatasetSource`, but your "
                "`UCVolumeDatasetSource` might be invalid."
            )
            return

        try:
            # Check if `self.path` points to a valid UC file.
            w.files.get_metadata(self.path)
        except Exception:
            try:
                # Check if `self.path` points to a valid UC directory.
                w.files.get_directory_metadata(self.path)
                # Append a slash to `self.path` to indicate it's a directory.
                self.path += "/" if not self.path.endswith("/") else ""
            except Exception:
                # Neither file nor directory exists, we throw an exception.
                raise QCFlowException(f"{self.path} does not exist in Databricks Unified Catalog.")

    @staticmethod
    def _get_source_type() -> str:
        return "uc_volume"

    @staticmethod
    def _can_resolve(raw_source: Any):
        raise NotImplementedError

    @classmethod
    def _resolve(cls, raw_source: str):
        raise NotImplementedError

    def to_dict(self) -> dict[Any, Any]:
        return {"path": self.path}

    @classmethod
    def from_dict(cls, source_dict: dict[Any, Any]) -> "UCVolumeDatasetSource":
        return cls(**source_dict)