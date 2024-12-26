import os

import pytest


@pytest.fixture(autouse=True)
def is_skinny():
    if "QCFLOW_SKINNY" not in os.environ:
        pytest.skip("This test is only valid for the skinny client")


def test_fails_import_flask():
    import qcflow  # noqa: F401

    with pytest.raises(ImportError, match="flask"):
        import flask  # noqa: F401


def test_fails_import_pandas():
    import qcflow  # noqa: F401

    with pytest.raises(ImportError, match="pandas"):
        import pandas  # noqa: F401


def test_fails_import_numpy():
    import qcflow  # noqa: F401

    with pytest.raises(ImportError, match="numpy"):
        import numpy  # noqa: F401
