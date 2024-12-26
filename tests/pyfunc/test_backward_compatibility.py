import pytest

import qcflow


@pytest.mark.parametrize("version", ["2.7.1", "2.8.1"])
def test_backward_compatibility(version):
    model = qcflow.pyfunc.load_model(f"tests/resources/pyfunc_models/{version}")
    assert model.predict("QCFlow is great!") == "QCFlow is great!"
