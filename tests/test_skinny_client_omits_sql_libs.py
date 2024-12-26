import os

import pytest


@pytest.mark.skipif(
    "QCFLOW_SKINNY" not in os.environ, reason="This test is only valid for the skinny client"
)
def test_fails_import_sqlalchemy():
    import qcflow  # noqa: F401

    with pytest.raises(ImportError, match="sqlalchemy"):
        import sqlalchemy  # noqa: F401
