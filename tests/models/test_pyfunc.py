QCFLOW_VERSION = "1.0.0"  # we expect this model to be bound to this qcflow version.


class PyFuncTestModel:
    def __init__(self, check_version=True):
        self._check_version = check_version

    def predict(self, df):
        from qcflow.version import VERSION

        if self._check_version:
            assert VERSION == QCFLOW_VERSION
        mu = df.mean().mean()
        return [mu for _ in range(len(df))]


def _load_pyfunc(_):
    return PyFuncTestModel()
