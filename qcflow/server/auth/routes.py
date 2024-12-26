from qcflow.server.handlers import _get_rest_path

HOME = "/"
SIGNUP = "/signup"
CREATE_USER = _get_rest_path("/qcflow/users/create")
GET_USER = _get_rest_path("/qcflow/users/get")
UPDATE_USER_PASSWORD = _get_rest_path("/qcflow/users/update-password")
UPDATE_USER_ADMIN = _get_rest_path("/qcflow/users/update-admin")
DELETE_USER = _get_rest_path("/qcflow/users/delete")
CREATE_EXPERIMENT_PERMISSION = _get_rest_path("/qcflow/experiments/permissions/create")
GET_EXPERIMENT_PERMISSION = _get_rest_path("/qcflow/experiments/permissions/get")
UPDATE_EXPERIMENT_PERMISSION = _get_rest_path("/qcflow/experiments/permissions/update")
DELETE_EXPERIMENT_PERMISSION = _get_rest_path("/qcflow/experiments/permissions/delete")
CREATE_REGISTERED_MODEL_PERMISSION = _get_rest_path("/qcflow/registered-models/permissions/create")
GET_REGISTERED_MODEL_PERMISSION = _get_rest_path("/qcflow/registered-models/permissions/get")
UPDATE_REGISTERED_MODEL_PERMISSION = _get_rest_path("/qcflow/registered-models/permissions/update")
DELETE_REGISTERED_MODEL_PERMISSION = _get_rest_path("/qcflow/registered-models/permissions/delete")
