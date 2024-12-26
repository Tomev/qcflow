from qcflow import pyfunc
from qcflow.pyfunc import scoring_server

app = scoring_server.init(pyfunc.load_model("/opt/ml/model/"))
