import pytest

import qcflow.spark
from qcflow.exceptions import MlflowException

from tests.spark.autologging.utils import _get_or_create_spark_session


def test_enabling_autologging_throws_for_missing_jar():
    with _get_or_create_spark_session(jars=""):
        with pytest.raises(MlflowException, match="ensure you have the qcflow-spark JAR attached"):
            qcflow.spark.autolog()
