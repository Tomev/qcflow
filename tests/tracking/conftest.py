import pytest

import qcflow


@pytest.fixture
def reset_active_experiment():
    yield
    qcflow.tracking.fluent._active_experiment_id = None
