import os

import pytest


@pytest.mark.skipif(
    "QCFLOW_SKINNY" not in os.environ, reason="This test is only valid for the skinny client"
)
def test_autolog_without_scipy():
    import qcflow

    with pytest.raises(ImportError, match="scipy"):
        import scipy  # noqa: F401

    assert not qcflow.models.utils.HAS_SCIPY

    qcflow.autolog()
    qcflow.models.utils._Example({})
