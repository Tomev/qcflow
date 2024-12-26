# QCFlow Keras 3 flavor.
import keras
from packaging.version import Version

if Version(keras.__version__) < Version("3.0.0"):
    from qcflow.tensorflow import (
        # Redirect `qcflow.keras._load_pyfunc` to `qcflow.tensorflow._load_pyfunc`,
        # For backwards compatibility on loading keras model saved by old qcflow versions.
        _load_pyfunc,
        autolog,
        load_model,
        log_model,
        save_model,
    )

    __all__ = [
        "_load_pyfunc",
        "autolog",
        "load_model",
        "save_model",
        "log_model",
    ]
else:
    from qcflow.keras.autologging import autolog
    from qcflow.keras.callback import MlflowCallback
    from qcflow.keras.load import _load_pyfunc, load_model
    from qcflow.keras.save import (
        get_default_conda_env,
        get_default_pip_requirements,
        log_model,
        save_model,
    )

    FLAVOR_NAME = "keras"

    QCFlowCallback = MlflowCallback  # for backwards compatibility

    __all__ = [
        "_load_pyfunc",
        "MlflowCallback",
        "QCFlowCallback",
        "autolog",
        "load_model",
        "save_model",
        "log_model",
        "get_default_pip_requirements",
        "get_default_conda_env",
    ]
