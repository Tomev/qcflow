import getpass
import sys

from qcflow.entities import SourceType
from qcflow.tracking.context.abstract_context import RunContextProvider
from qcflow.utils.credentials import read_qcflow_creds
from qcflow.utils.qcflow_tags import (
    QCFLOW_SOURCE_NAME,
    QCFLOW_SOURCE_TYPE,
    QCFLOW_USER,
)

_DEFAULT_USER = "unknown"


def _get_user():
    """Get the current computer username."""
    try:
        return getpass.getuser()
    except ImportError:
        return _DEFAULT_USER


def _get_main_file():
    if len(sys.argv) > 0:
        return sys.argv[0]
    return None


def _get_source_name():
    main_file = _get_main_file()
    if main_file is not None:
        return main_file
    return "<console>"


def _get_source_type():
    return SourceType.LOCAL


class DefaultRunContext(RunContextProvider):
    def in_context(self):
        return True

    def tags(self):
        creds = read_qcflow_creds()
        return {
            QCFLOW_USER: creds.username or _get_user(),
            QCFLOW_SOURCE_NAME: _get_source_name(),
            QCFLOW_SOURCE_TYPE: SourceType.to_string(_get_source_type()),
        }
