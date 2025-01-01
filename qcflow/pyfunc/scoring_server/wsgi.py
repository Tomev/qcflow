import os

from qcflow.pyfunc import scoring_server

app = scoring_server.init(
    scoring_server.load_model_with_qcflow_config(os.environ[scoring_server._SERVER_MODEL_PATH])
)
