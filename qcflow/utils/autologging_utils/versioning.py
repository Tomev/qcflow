import importlib
import importlib.metadata
import re
from typing import Literal

from packaging.version import InvalidVersion, Version

from qcflow.ml_package_versions import _ML_PACKAGE_VERSIONS, FLAVOR_TO_MODULE_NAME
from qcflow.utils.databricks_utils import is_in_databricks_runtime


def _check_version_in_range(ver, min_ver, max_ver):
    return Version(min_ver) <= Version(ver) <= Version(max_ver)


def _check_spark_version_in_range(ver, min_ver, max_ver):
    """
    Utility function for allowing late addition release changes to PySpark minor version increments
    to be accepted, provided that the previous minor version has been previously validated.
    For example, if version 3.2.1 has been validated as functional with QCFlow, an upgrade of
    PySpark's minor version to 3.2.2 will still provide a valid version check.
    """
    parsed_ver = Version(ver)
    if parsed_ver > Version(min_ver):
        ver = f"{parsed_ver.major}.{parsed_ver.minor}"
    return _check_version_in_range(ver, min_ver, max_ver)


def _violates_pep_440(ver):
    try:
        Version(ver)
        return False
    except InvalidVersion:
        return True


def _is_pre_or_dev_release(ver):
    v = Version(ver)
    return v.is_devrelease or v.is_prerelease


def _strip_dev_version_suffix(version):
    return re.sub(r"(\.?)dev.*", "", version)


def get_min_max_version_and_pip_release(
    flavor_name: str, category: Literal["autologging", "models"] = "autologging"
):
    if flavor_name == "pyspark.ml":
        # pyspark.ml is a special case of spark flavor
        flavor_name = "spark"

    min_version = _ML_PACKAGE_VERSIONS[flavor_name][category]["minimum"]
    max_version = _ML_PACKAGE_VERSIONS[flavor_name][category]["maximum"]
    pip_release = _ML_PACKAGE_VERSIONS[flavor_name]["package_info"]["pip_release"]
    return min_version, max_version, pip_release


def is_flavor_supported_for_associated_package_versions(flavor_name):
    """
    Returns:
        True if the specified flavor is supported for the currently-installed versions of its
        associated packages.
    """
    module_name = FLAVOR_TO_MODULE_NAME[flavor_name]

    try:
        actual_version = importlib.import_module(module_name).__version__
    except AttributeError:
        try:
            # NB: Module name is not necessarily the same as the package name. However,
            # we assume they are the same here for simplicity. If they are not the same,
            # this will fail and fallback to 'True', which is not a disaster.
            actual_version = importlib.metadata.version(module_name)
        except importlib.metadata.PackageNotFoundError:
            # Some package (e.g. dspy) do not publish version info in a standard format.
            # For this case, we assume the package version is supported by QCFlow.
            return True

    # In Databricks, treat 'pyspark 3.x.y.dev0' as 'pyspark 3.x.y'
    if module_name == "pyspark" and is_in_databricks_runtime():
        actual_version = _strip_dev_version_suffix(actual_version)

    if _violates_pep_440(actual_version) or _is_pre_or_dev_release(actual_version):
        return False
    min_version, max_version, _ = get_min_max_version_and_pip_release(flavor_name)

    if module_name == "pyspark" and is_in_databricks_runtime():
        # QCFlow 1.25.0 is known to be compatible with PySpark 3.3.0 on Databricks, despite the
        # fact that PySpark 3.3.0 was not available in PyPI at the time of the QCFlow 1.25.0 release
        if Version(max_version) < Version("3.3.0"):
            max_version = "3.3.0"
        return _check_spark_version_in_range(actual_version, min_version, max_version)
    else:
        return _check_version_in_range(actual_version, min_version, max_version)
