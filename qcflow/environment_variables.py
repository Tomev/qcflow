"""
This module defines environment variables used in QCFlow.
"""

import os
from pathlib import Path


class _EnvironmentVariable:
    """
    Represents an environment variable.
    """

    def __init__(self, name, type_, default):
        self.name = name
        self.type = type_
        self.default = default

    @property
    def defined(self):
        return self.name in os.environ

    def get_raw(self):
        return os.getenv(self.name)

    def set(self, value):
        os.environ[self.name] = str(value)

    def unset(self):
        os.environ.pop(self.name, None)

    def get(self):
        """
        Reads the value of the environment variable if it exists and converts it to the desired
        type. Otherwise, returns the default value.
        """
        if (val := self.get_raw()) is not None:
            try:
                return self.type(val)
            except Exception as e:
                raise ValueError(f"Failed to convert {val!r} to {self.type} for {self.name}: {e}")
        return self.default

    def __str__(self):
        return f"{self.name} (default: {self.default}, type: {self.type.__name__})"

    def __repr__(self):
        return repr(self.name)

    def __format__(self, format_spec: str) -> str:
        return self.name.__format__(format_spec)


class _BooleanEnvironmentVariable(_EnvironmentVariable):
    """
    Represents a boolean environment variable.
    """

    def __init__(self, name, default):
        # `default not in [True, False, None]` doesn't work because `1 in [True]`
        # (or `0 in [False]`) returns True.
        if not (default is True or default is False or default is None):
            raise ValueError(f"{name} default value must be one of [True, False, None]")
        super().__init__(name, bool, default)

    def get(self):
        if not self.defined:
            return self.default

        val = os.getenv(self.name)
        lowercased = val.lower()
        if lowercased not in ["true", "false", "1", "0"]:
            raise ValueError(
                f"{self.name} value must be one of ['true', 'false', '1', '0'] (case-insensitive), "
                f"but got {val}"
            )
        return lowercased in ["true", "1"]


#: Specifies the tracking URI.
#: (default: ``None``)
QCFLOW_TRACKING_URI = _EnvironmentVariable("QCFLOW_TRACKING_URI", str, None)

#: Specifies the registry URI.
#: (default: ``None``)
QCFLOW_REGISTRY_URI = _EnvironmentVariable("QCFLOW_REGISTRY_URI", str, None)

#: Specifies the ``dfs_tmpdir`` parameter to use for ``qcflow.spark.save_model``,
#: ``qcflow.spark.log_model`` and ``qcflow.spark.load_model``. See
#: https://www.qcflow.org/docs/latest/python_api/qcflow.spark.html#qcflow.spark.save_model
#: for more information.
#: (default: ``/tmp/qcflow``)
QCFLOW_DFS_TMP = _EnvironmentVariable("QCFLOW_DFS_TMP", str, "/tmp/qcflow")

#: Specifies the maximum number of retries for QCFlow HTTP requests
#: (default: ``5``)
QCFLOW_HTTP_REQUEST_MAX_RETRIES = _EnvironmentVariable("QCFLOW_HTTP_REQUEST_MAX_RETRIES", int, 5)

#: Specifies the backoff increase factor between QCFlow HTTP request failures
#: (default: ``2``)
QCFLOW_HTTP_REQUEST_BACKOFF_FACTOR = _EnvironmentVariable(
    "QCFLOW_HTTP_REQUEST_BACKOFF_FACTOR", int, 2
)

#: Specifies the backoff jitter between QCFlow HTTP request failures
#: (default: ``1.0``)
QCFLOW_HTTP_REQUEST_BACKOFF_JITTER = _EnvironmentVariable(
    "QCFLOW_HTTP_REQUEST_BACKOFF_JITTER", float, 1.0
)

#: Specifies the timeout in seconds for QCFlow HTTP requests
#: (default: ``120``)
QCFLOW_HTTP_REQUEST_TIMEOUT = _EnvironmentVariable("QCFLOW_HTTP_REQUEST_TIMEOUT", int, 120)

#: Specifies whether to respect Retry-After header on status codes defined as
#: Retry.RETRY_AFTER_STATUS_CODES or not for QCFlow HTTP request
#: (default: ``True``)
QCFLOW_HTTP_RESPECT_RETRY_AFTER_HEADER = _BooleanEnvironmentVariable(
    "QCFLOW_HTTP_RESPECT_RETRY_AFTER_HEADER", True
)

#: Internal-only configuration that sets an upper bound to the allowable maximum
#: retries for HTTP requests
#: (default: ``10``)
_QCFLOW_HTTP_REQUEST_MAX_RETRIES_LIMIT = _EnvironmentVariable(
    "_QCFLOW_HTTP_REQUEST_MAX_RETRIES_LIMIT", int, 10
)

#: Internal-only configuration that sets the upper bound for an HTTP backoff_factor
#: (default: ``120``)
_QCFLOW_HTTP_REQUEST_MAX_BACKOFF_FACTOR_LIMIT = _EnvironmentVariable(
    "_QCFLOW_HTTP_REQUEST_MAX_BACKOFF_FACTOR_LIMIT", int, 120
)

#: Specifies whether QCFlow HTTP requests should be signed using AWS signature V4. It will overwrite
#: (default: ``False``). When set, it will overwrite the "Authorization" HTTP header.
#: See https://docs.aws.amazon.com/general/latest/gr/signature-version-4.html for more information.
QCFLOW_TRACKING_AWS_SIGV4 = _BooleanEnvironmentVariable("QCFLOW_TRACKING_AWS_SIGV4", False)

#: Specifies the auth provider to sign the QCFlow HTTP request
#: (default: ``None``). When set, it will overwrite the "Authorization" HTTP header.
QCFLOW_TRACKING_AUTH = _EnvironmentVariable("QCFLOW_TRACKING_AUTH", str, None)

#: Specifies the chunk size to use when downloading a file from GCS
#: (default: ``None``). If None, the chunk size is automatically determined by the
#: ``google-cloud-storage`` package.
QCFLOW_GCS_DOWNLOAD_CHUNK_SIZE = _EnvironmentVariable("QCFLOW_GCS_DOWNLOAD_CHUNK_SIZE", int, None)

#: Specifies the chunk size to use when uploading a file to GCS.
#: (default: ``None``). If None, the chunk size is automatically determined by the
#: ``google-cloud-storage`` package.
QCFLOW_GCS_UPLOAD_CHUNK_SIZE = _EnvironmentVariable("QCFLOW_GCS_UPLOAD_CHUNK_SIZE", int, None)

#: (Deprecated, please use ``QCFLOW_ARTIFACT_UPLOAD_DOWNLOAD_TIMEOUT``)
#: Specifies the default timeout to use when downloading/uploading a file from/to GCS
#: (default: ``None``). If None, ``google.cloud.storage.constants._DEFAULT_TIMEOUT`` is used.
QCFLOW_GCS_DEFAULT_TIMEOUT = _EnvironmentVariable("QCFLOW_GCS_DEFAULT_TIMEOUT", int, None)

#: Specifies whether to disable model logging and loading via qcflowdbfs.
#: (default: ``None``)
_DISABLE_QCFLOWDBFS = _EnvironmentVariable("DISABLE_QCFLOWDBFS", str, None)

#: Specifies the S3 endpoint URL to use for S3 artifact operations.
#: (default: ``None``)
QCFLOW_S3_ENDPOINT_URL = _EnvironmentVariable("QCFLOW_S3_ENDPOINT_URL", str, None)

#: Specifies whether or not to skip TLS certificate verification for S3 artifact operations.
#: (default: ``False``)
QCFLOW_S3_IGNORE_TLS = _BooleanEnvironmentVariable("QCFLOW_S3_IGNORE_TLS", False)

#: Specifies extra arguments for S3 artifact uploads.
#: (default: ``None``)
QCFLOW_S3_UPLOAD_EXTRA_ARGS = _EnvironmentVariable("QCFLOW_S3_UPLOAD_EXTRA_ARGS", str, None)

#: Specifies the location of a Kerberos ticket cache to use for HDFS artifact operations.
#: (default: ``None``)
QCFLOW_KERBEROS_TICKET_CACHE = _EnvironmentVariable("QCFLOW_KERBEROS_TICKET_CACHE", str, None)

#: Specifies a Kerberos user for HDFS artifact operations.
#: (default: ``None``)
QCFLOW_KERBEROS_USER = _EnvironmentVariable("QCFLOW_KERBEROS_USER", str, None)

#: Specifies extra pyarrow configurations for HDFS artifact operations.
#: (default: ``None``)
QCFLOW_PYARROW_EXTRA_CONF = _EnvironmentVariable("QCFLOW_PYARROW_EXTRA_CONF", str, None)

#: Specifies the ``pool_size`` parameter to use for ``sqlalchemy.create_engine`` in the SQLAlchemy
#: tracking store. See https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine.params.pool_size
#: for more information.
#: (default: ``None``)
QCFLOW_SQLALCHEMYSTORE_POOL_SIZE = _EnvironmentVariable(
    "QCFLOW_SQLALCHEMYSTORE_POOL_SIZE", int, None
)

#: Specifies the ``pool_recycle`` parameter to use for ``sqlalchemy.create_engine`` in the
#: SQLAlchemy tracking store. See https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine.params.pool_recycle
#: for more information.
#: (default: ``None``)
QCFLOW_SQLALCHEMYSTORE_POOL_RECYCLE = _EnvironmentVariable(
    "QCFLOW_SQLALCHEMYSTORE_POOL_RECYCLE", int, None
)

#: Specifies the ``max_overflow`` parameter to use for ``sqlalchemy.create_engine`` in the
#: SQLAlchemy tracking store. See https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine.params.max_overflow
#: for more information.
#: (default: ``None``)
QCFLOW_SQLALCHEMYSTORE_MAX_OVERFLOW = _EnvironmentVariable(
    "QCFLOW_SQLALCHEMYSTORE_MAX_OVERFLOW", int, None
)

#: Specifies the ``echo`` parameter to use for ``sqlalchemy.create_engine`` in the
#: SQLAlchemy tracking store. See https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine.params.echo
#: for more information.
#: (default: ``False``)
QCFLOW_SQLALCHEMYSTORE_ECHO = _BooleanEnvironmentVariable("QCFLOW_SQLALCHEMYSTORE_ECHO", False)

#: Specifies whether or not to print a warning when `--env-manager=conda` is specified.
#: (default: ``False``)
QCFLOW_DISABLE_ENV_MANAGER_CONDA_WARNING = _BooleanEnvironmentVariable(
    "QCFLOW_DISABLE_ENV_MANAGER_CONDA_WARNING", False
)
#: Specifies the ``poolclass`` parameter to use for ``sqlalchemy.create_engine`` in the
#: SQLAlchemy tracking store. See https://docs.sqlalchemy.org/en/14/core/engines.html#sqlalchemy.create_engine.params.poolclass
#: for more information.
#: (default: ``None``)
QCFLOW_SQLALCHEMYSTORE_POOLCLASS = _EnvironmentVariable(
    "QCFLOW_SQLALCHEMYSTORE_POOLCLASS", str, None
)

#: Specifies the ``timeout_seconds`` for QCFlow Model dependency inference operations.
#: (default: ``120``)
QCFLOW_REQUIREMENTS_INFERENCE_TIMEOUT = _EnvironmentVariable(
    "QCFLOW_REQUIREMENTS_INFERENCE_TIMEOUT", int, 120
)

#: Specifies the QCFlow Model Scoring server request timeout in seconds
#: (default: ``60``)
QCFLOW_SCORING_SERVER_REQUEST_TIMEOUT = _EnvironmentVariable(
    "QCFLOW_SCORING_SERVER_REQUEST_TIMEOUT", int, 60
)

#: (Experimental, may be changed or removed)
#: Specifies the timeout to use when uploading or downloading a file
#: (default: ``None``). If None, individual artifact stores will choose defaults.
QCFLOW_ARTIFACT_UPLOAD_DOWNLOAD_TIMEOUT = _EnvironmentVariable(
    "QCFLOW_ARTIFACT_UPLOAD_DOWNLOAD_TIMEOUT", int, None
)

#: Specifies the timeout for model inference with input example(s) when logging/saving a model.
#: QCFlow runs a few inference requests against the model to infer model signature and pip
#: requirements. Sometimes the prediction hangs for a long time, especially for a large model.
#: This timeout limits the allowable time for performing a prediction for signature inference
#: and will abort the prediction, falling back to the default signature and pip requirements.
QCFLOW_INPUT_EXAMPLE_INFERENCE_TIMEOUT = _EnvironmentVariable(
    "QCFLOW_INPUT_EXAMPLE_INFERENCE_TIMEOUT", int, 180
)


#: Specifies the device intended for use in the predict function - can be used
#: to override behavior where the GPU is used by default when available by
#: setting this environment variable to be ``cpu``. Currently, this
#: variable is only supported for the QCFlow PyTorch and HuggingFace flavors.
#: For the HuggingFace flavor, note that device must be parseable as an integer.
QCFLOW_DEFAULT_PREDICTION_DEVICE = _EnvironmentVariable(
    "QCFLOW_DEFAULT_PREDICTION_DEVICE", str, None
)

#: Specifies to Huggingface whether to use the automatic device placement logic of
# HuggingFace accelerate. If it's set to false, the low_cpu_mem_usage flag will not be
# set to True and device_map will not be set to "auto".
QCFLOW_HUGGINGFACE_DISABLE_ACCELERATE_FEATURES = _BooleanEnvironmentVariable(
    "QCFLOW_DISABLE_HUGGINGFACE_ACCELERATE_FEATURES", False
)

#: Specifies to Huggingface whether to use the automatic device placement logic of
# HuggingFace accelerate. If it's set to false, the low_cpu_mem_usage flag will not be
# set to True and device_map will not be set to "auto". Default to False.
QCFLOW_HUGGINGFACE_USE_DEVICE_MAP = _BooleanEnvironmentVariable(
    "QCFLOW_HUGGINGFACE_USE_DEVICE_MAP", False
)

#: Specifies to Huggingface to use the automatic device placement logic of HuggingFace accelerate.
#: This can be set to values supported by the version of HuggingFace Accelerate being installed.
QCFLOW_HUGGINGFACE_DEVICE_MAP_STRATEGY = _EnvironmentVariable(
    "QCFLOW_HUGGINGFACE_DEVICE_MAP_STRATEGY", str, "auto"
)

#: Specifies to Huggingface to use the low_cpu_mem_usage flag powered by HuggingFace accelerate.
#: If it's set to false, the low_cpu_mem_usage flag will be set to False.
QCFLOW_HUGGINGFACE_USE_LOW_CPU_MEM_USAGE = _BooleanEnvironmentVariable(
    "QCFLOW_HUGGINGFACE_USE_LOW_CPU_MEM_USAGE", True
)

#: Specifies the max_shard_size to use when qcflow transformers flavor saves the model checkpoint.
#: This can be set to override the 500MB default.
QCFLOW_HUGGINGFACE_MODEL_MAX_SHARD_SIZE = _EnvironmentVariable(
    "QCFLOW_HUGGINGFACE_MODEL_MAX_SHARD_SIZE", str, "500MB"
)

#: Specifies the name of the Databricks secret scope to use for storing OpenAI API keys.
QCFLOW_OPENAI_SECRET_SCOPE = _EnvironmentVariable("QCFLOW_OPENAI_SECRET_SCOPE", str, None)

#: (Experimental, may be changed or removed)
#: Specifies the download options to be used by pip wheel when `add_libraries_to_model` is used to
#: create and log model dependencies as model artifacts. The default behavior only uses dependency
#: binaries and no source packages.
#: (default: ``--only-binary=:all:``).
QCFLOW_WHEELED_MODEL_PIP_DOWNLOAD_OPTIONS = _EnvironmentVariable(
    "QCFLOW_WHEELED_MODEL_PIP_DOWNLOAD_OPTIONS", str, "--only-binary=:all:"
)

# Specifies whether or not to use multipart download when downloading a large file on Databricks.
QCFLOW_ENABLE_MULTIPART_DOWNLOAD = _BooleanEnvironmentVariable(
    "QCFLOW_ENABLE_MULTIPART_DOWNLOAD", True
)

# Specifies whether or not to use multipart upload when uploading large artifacts.
QCFLOW_ENABLE_MULTIPART_UPLOAD = _BooleanEnvironmentVariable("QCFLOW_ENABLE_MULTIPART_UPLOAD", True)

#: Specifies whether or not to use multipart upload for proxied artifact access.
#: (default: ``False``)
QCFLOW_ENABLE_PROXY_MULTIPART_UPLOAD = _BooleanEnvironmentVariable(
    "QCFLOW_ENABLE_PROXY_MULTIPART_UPLOAD", False
)

#: Private environment variable that's set to ``True`` while running tests.
_QCFLOW_TESTING = _BooleanEnvironmentVariable("QCFLOW_TESTING", False)

#: Specifies the username used to authenticate with a tracking server.
#: (default: ``None``)
QCFLOW_TRACKING_USERNAME = _EnvironmentVariable("QCFLOW_TRACKING_USERNAME", str, None)

#: Specifies the password used to authenticate with a tracking server.
#: (default: ``None``)
QCFLOW_TRACKING_PASSWORD = _EnvironmentVariable("QCFLOW_TRACKING_PASSWORD", str, None)

#: Specifies and takes precedence for setting the basic/bearer auth on http requests.
#: (default: ``None``)
QCFLOW_TRACKING_TOKEN = _EnvironmentVariable("QCFLOW_TRACKING_TOKEN", str, None)

#: Specifies whether to verify TLS connection in ``requests.request`` function,
#: see https://requests.readthedocs.io/en/master/api/
#: (default: ``False``).
QCFLOW_TRACKING_INSECURE_TLS = _BooleanEnvironmentVariable("QCFLOW_TRACKING_INSECURE_TLS", False)

#: Sets the ``verify`` param in ``requests.request`` function,
#: see https://requests.readthedocs.io/en/master/api/
#: (default: ``None``)
QCFLOW_TRACKING_SERVER_CERT_PATH = _EnvironmentVariable(
    "QCFLOW_TRACKING_SERVER_CERT_PATH", str, None
)

#: Sets the ``cert`` param in ``requests.request`` function,
#: see https://requests.readthedocs.io/en/master/api/
#: (default: ``None``)
QCFLOW_TRACKING_CLIENT_CERT_PATH = _EnvironmentVariable(
    "QCFLOW_TRACKING_CLIENT_CERT_PATH", str, None
)

#: Specified the ID of the run to log data to.
#: (default: ``None``)
QCFLOW_RUN_ID = _EnvironmentVariable("QCFLOW_RUN_ID", str, None)

#: Specifies the default root directory for tracking `FileStore`.
#: (default: ``None``)
QCFLOW_TRACKING_DIR = _EnvironmentVariable("QCFLOW_TRACKING_DIR", str, None)

#: Specifies the default root directory for registry `FileStore`.
#: (default: ``None``)
QCFLOW_REGISTRY_DIR = _EnvironmentVariable("QCFLOW_REGISTRY_DIR", str, None)

#: Specifies the default experiment ID to create run to.
#: (default: ``None``)
QCFLOW_EXPERIMENT_ID = _EnvironmentVariable("QCFLOW_EXPERIMENT_ID", str, None)

#: Specifies the default experiment name to create run to.
#: (default: ``None``)
QCFLOW_EXPERIMENT_NAME = _EnvironmentVariable("QCFLOW_EXPERIMENT_NAME", str, None)

#: Specified the path to the configuration file for QCFlow Authentication.
#: (default: ``None``)
QCFLOW_AUTH_CONFIG_PATH = _EnvironmentVariable("QCFLOW_AUTH_CONFIG_PATH", str, None)

#: Specifies and takes precedence for setting the UC OSS basic/bearer auth on http requests.
#: (default: ``None``)
QCFLOW_UC_OSS_TOKEN = _EnvironmentVariable("QCFLOW_UC_OSS_TOKEN", str, None)

#: Specifies the root directory to create Python virtual environments in.
#: (default: ``~/.qcflow/envs``)
QCFLOW_ENV_ROOT = _EnvironmentVariable(
    "QCFLOW_ENV_ROOT", str, str(Path.home().joinpath(".qcflow", "envs"))
)

#: Specifies whether or not to use DBFS FUSE mount to store artifacts on Databricks
#: (default: ``False``)
QCFLOW_ENABLE_DBFS_FUSE_ARTIFACT_REPO = _BooleanEnvironmentVariable(
    "QCFLOW_ENABLE_DBFS_FUSE_ARTIFACT_REPO", True
)

#: Specifies whether or not to use UC Volume FUSE mount to store artifacts on Databricks
#: (default: ``True``)
QCFLOW_ENABLE_UC_VOLUME_FUSE_ARTIFACT_REPO = _BooleanEnvironmentVariable(
    "QCFLOW_ENABLE_UC_VOLUME_FUSE_ARTIFACT_REPO", True
)

#: Private environment variable that should be set to ``True`` when running autologging tests.
#: (default: ``False``)
_QCFLOW_AUTOLOGGING_TESTING = _BooleanEnvironmentVariable("QCFLOW_AUTOLOGGING_TESTING", False)

#: (Experimental, may be changed or removed)
#: Specifies the uri of a QCFlow Gateway Server instance to be used with the Gateway Client APIs
#: (default: ``None``)
QCFLOW_GATEWAY_URI = _EnvironmentVariable("QCFLOW_GATEWAY_URI", str, None)

#: (Experimental, may be changed or removed)
#: Specifies the uri of an QCFlow AI Gateway instance to be used with the Deployments
#: Client APIs
#: (default: ``None``)
QCFLOW_DEPLOYMENTS_TARGET = _EnvironmentVariable("QCFLOW_DEPLOYMENTS_TARGET", str, None)

#: Specifies the path of the config file for QCFlow AI Gateway.
#: (default: ``None``)
QCFLOW_GATEWAY_CONFIG = _EnvironmentVariable("QCFLOW_GATEWAY_CONFIG", str, None)

#: Specifies the path of the config file for QCFlow AI Gateway.
#: (default: ``None``)
QCFLOW_DEPLOYMENTS_CONFIG = _EnvironmentVariable("QCFLOW_DEPLOYMENTS_CONFIG", str, None)

#: Specifies whether to display the progress bar when uploading/downloading artifacts.
#: (default: ``True``)
QCFLOW_ENABLE_ARTIFACTS_PROGRESS_BAR = _BooleanEnvironmentVariable(
    "QCFLOW_ENABLE_ARTIFACTS_PROGRESS_BAR", True
)

#: Specifies the conda home directory to use.
#: (default: ``conda``)
QCFLOW_CONDA_HOME = _EnvironmentVariable("QCFLOW_CONDA_HOME", str, None)

#: Specifies the name of the command to use when creating the environments.
#: For example, let's say we want to use mamba (https://github.com/mamba-org/mamba)
#: instead of conda to create environments.
#: Then: > conda install mamba -n base -c conda-forge
#: If not set, use the same as conda_path
#: (default: ``conda``)
QCFLOW_CONDA_CREATE_ENV_CMD = _EnvironmentVariable("QCFLOW_CONDA_CREATE_ENV_CMD", str, "conda")

#: Specifies the execution directory for recipes.
#: (default: ``None``)
QCFLOW_RECIPES_EXECUTION_DIRECTORY = _EnvironmentVariable(
    "QCFLOW_RECIPES_EXECUTION_DIRECTORY", str, None
)

#: Specifies the target step to execute for recipes.
#: (default: ``None``)
QCFLOW_RECIPES_EXECUTION_TARGET_STEP_NAME = _EnvironmentVariable(
    "QCFLOW_RECIPES_EXECUTION_TARGET_STEP_NAME", str, None
)

#: Specifies the flavor to serve in the scoring server.
#: (default ``None``)
QCFLOW_DEPLOYMENT_FLAVOR_NAME = _EnvironmentVariable("QCFLOW_DEPLOYMENT_FLAVOR_NAME", str, None)

#: Specifies the profile to use for recipes.
#: (default: ``None``)
QCFLOW_RECIPES_PROFILE = _EnvironmentVariable("QCFLOW_RECIPES_PROFILE", str, None)

#: Specifies the QCFlow Run context
#: (default: ``None``)
QCFLOW_RUN_CONTEXT = _EnvironmentVariable("QCFLOW_RUN_CONTEXT", str, None)

#: Specifies the URL of the ECR-hosted Docker image a model is deployed into for SageMaker.
# (default: ``None``)
QCFLOW_SAGEMAKER_DEPLOY_IMG_URL = _EnvironmentVariable("QCFLOW_SAGEMAKER_DEPLOY_IMG_URL", str, None)

#: Specifies whether to disable creating a new conda environment for `qcflow models build-docker`.
#: (default: ``False``)
QCFLOW_DISABLE_ENV_CREATION = _BooleanEnvironmentVariable("QCFLOW_DISABLE_ENV_CREATION", False)

#: Specifies the timeout value for downloading chunks of qcflow artifacts.
#: (default: ``300``)
QCFLOW_DOWNLOAD_CHUNK_TIMEOUT = _EnvironmentVariable("QCFLOW_DOWNLOAD_CHUNK_TIMEOUT", int, 300)

#: Specifies if system metrics logging should be enabled.
QCFLOW_ENABLE_SYSTEM_METRICS_LOGGING = _BooleanEnvironmentVariable(
    "QCFLOW_ENABLE_SYSTEM_METRICS_LOGGING", False
)

#: Specifies the sampling interval for system metrics logging.
QCFLOW_SYSTEM_METRICS_SAMPLING_INTERVAL = _EnvironmentVariable(
    "QCFLOW_SYSTEM_METRICS_SAMPLING_INTERVAL", float, None
)

#: Specifies the number of samples before logging system metrics.
QCFLOW_SYSTEM_METRICS_SAMPLES_BEFORE_LOGGING = _EnvironmentVariable(
    "QCFLOW_SYSTEM_METRICS_SAMPLES_BEFORE_LOGGING", int, None
)

#: Specifies the node id of system metrics logging. This is useful in multi-node (distributed
#: training) setup.
QCFLOW_SYSTEM_METRICS_NODE_ID = _EnvironmentVariable("QCFLOW_SYSTEM_METRICS_NODE_ID", str, None)


# Private environment variable to specify the number of chunk download retries for multipart
# download.
_QCFLOW_MPD_NUM_RETRIES = _EnvironmentVariable("_QCFLOW_MPD_NUM_RETRIES", int, 3)

# Private environment variable to specify the interval between chunk download retries for multipart
# download.
_QCFLOW_MPD_RETRY_INTERVAL_SECONDS = _EnvironmentVariable(
    "_QCFLOW_MPD_RETRY_INTERVAL_SECONDS", int, 1
)

#: Specifies the minimum file size in bytes to use multipart upload when logging artifacts
#: (default: ``524_288_000`` (500 MB))
QCFLOW_MULTIPART_UPLOAD_MINIMUM_FILE_SIZE = _EnvironmentVariable(
    "QCFLOW_MULTIPART_UPLOAD_MINIMUM_FILE_SIZE", int, 500 * 1024**2
)

#: Specifies the minimum file size in bytes to use multipart download when downloading artifacts
#: (default: ``524_288_000`` (500 MB))
QCFLOW_MULTIPART_DOWNLOAD_MINIMUM_FILE_SIZE = _EnvironmentVariable(
    "QCFLOW_MULTIPART_DOWNLOAD_MINIMUM_FILE_SIZE", int, 500 * 1024**2
)

#: Specifies the chunk size in bytes to use when performing multipart upload
#: (default: ``104_857_60`` (10 MB))
QCFLOW_MULTIPART_UPLOAD_CHUNK_SIZE = _EnvironmentVariable(
    "QCFLOW_MULTIPART_UPLOAD_CHUNK_SIZE", int, 10 * 1024**2
)

#: Specifies the chunk size in bytes to use when performing multipart download
#: (default: ``104_857_600`` (100 MB))
QCFLOW_MULTIPART_DOWNLOAD_CHUNK_SIZE = _EnvironmentVariable(
    "QCFLOW_MULTIPART_DOWNLOAD_CHUNK_SIZE", int, 100 * 1024**2
)

#: Specifies whether or not to allow the QCFlow server to follow redirects when
#: making HTTP requests. If set to False, the server will throw an exception if it
#: encounters a redirect response.
#: (default: ``True``)
QCFLOW_ALLOW_HTTP_REDIRECTS = _BooleanEnvironmentVariable("QCFLOW_ALLOW_HTTP_REDIRECTS", True)

# Specifies the timeout for deployment client APIs to declare a request has timed out
QCFLOW_DEPLOYMENT_PREDICT_TIMEOUT = _EnvironmentVariable(
    "QCFLOW_DEPLOYMENT_PREDICT_TIMEOUT", int, 120
)

QCFLOW_GATEWAY_RATE_LIMITS_STORAGE_URI = _EnvironmentVariable(
    "QCFLOW_GATEWAY_RATE_LIMITS_STORAGE_URI", str, None
)

#: If True, QCFlow fluent logging APIs, e.g., `qcflow.log_metric` will log asynchronously.
QCFLOW_ENABLE_ASYNC_LOGGING = _BooleanEnvironmentVariable("QCFLOW_ENABLE_ASYNC_LOGGING", False)

#: Number of workers in the thread pool used for asynchronous logging, defaults to 10.
QCFLOW_ASYNC_LOGGING_THREADPOOL_SIZE = _EnvironmentVariable(
    "QCFLOW_ASYNC_LOGGING_THREADPOOL_SIZE", int, 10
)

#: Specifies whether or not to have qcflow configure logging on import.
#: If set to True, qcflow will configure ``qcflow.<module_name>`` loggers with
#: logging handlers and formatters.
#: (default: ``True``)
QCFLOW_CONFIGURE_LOGGING = _BooleanEnvironmentVariable("QCFLOW_LOGGING_CONFIGURE_LOGGING", True)

#: If set to True, the following entities will be truncated to their maximum length:
#: - Param value
#: - Tag value
#: If set to False, an exception will be raised if the length of the entity exceeds the maximum
#: length.
#: (default: ``True``)
QCFLOW_TRUNCATE_LONG_VALUES = _BooleanEnvironmentVariable("QCFLOW_TRUNCATE_LONG_VALUES", True)

# Whether to run slow tests with pytest. Default to False in normal runs,
# but set to True in the weekly slow test jobs.
_QCFLOW_RUN_SLOW_TESTS = _BooleanEnvironmentVariable("QCFLOW_RUN_SLOW_TESTS", False)

#: The OpenJDK version to install in the Docker image used for QCFlow models.
#: (default: ``11``)
QCFLOW_DOCKER_OPENJDK_VERSION = _EnvironmentVariable("QCFLOW_DOCKER_OPENJDK_VERSION", str, "11")

# How many traces to be buffered at the Trace Client.
QCFLOW_TRACING_CLIENT_BUFFER_SIZE = _EnvironmentVariable(
    "QCFLOW_TRACING_CLIENT_BUFFER_SIZE", int, 1000
)

# How long a trace can be buffered at the in-memory trace client before being abandoned.
QCFLOW_TRACE_BUFFER_TTL_SECONDS = _EnvironmentVariable("QCFLOW_TRACE_BUFFER_TTL_SECONDS", int, 3600)

# How many traces to be buffered at the in-memory trace client.
QCFLOW_TRACE_BUFFER_MAX_SIZE = _EnvironmentVariable("QCFLOW_TRACE_BUFFER_MAX_SIZE", int, 1000)

#: Private configuration option.
#: Enables the ability to catch exceptions within QCFlow evaluate for classification models
#: where a class imbalance due to a missing target class would raise an error in the
#: underlying metrology modules (scikit-learn). If set to True, specific exceptions will be
#: caught, alerted via the warnings module, and evaluation will resume.
#: (default: ``False``)
_QCFLOW_EVALUATE_SUPPRESS_CLASSIFICATION_ERRORS = _BooleanEnvironmentVariable(
    "_QCFLOW_EVALUATE_SUPPRESS_CLASSIFICATION_ERRORS", False
)

#: Whether to warn (default) or raise (opt-in) for unresolvable requirements inference for
#: a model's dependency inference. If set to True, an exception will be raised if requirements
#: inference or the process of capturing imported modules encounters any errors.
QCFLOW_REQUIREMENTS_INFERENCE_RAISE_ERRORS = _BooleanEnvironmentVariable(
    "QCFLOW_REQUIREMENTS_INFERENCE_RAISE_ERRORS", False
)

# How many traces to display in Databricks Notebooks
QCFLOW_MAX_TRACES_TO_DISPLAY_IN_NOTEBOOK = _EnvironmentVariable(
    "QCFLOW_MAX_TRACES_TO_DISPLAY_IN_NOTEBOOK", int, 10
)

# Default addressing style to use for boto client
QCFLOW_BOTO_CLIENT_ADDRESSING_STYLE = _EnvironmentVariable(
    "QCFLOW_BOTO_CLIENT_ADDRESSING_STYLE", str, "auto"
)

#: Specify the timeout in seconds for Databricks endpoint HTTP request retries.
QCFLOW_DATABRICKS_ENDPOINT_HTTP_RETRY_TIMEOUT = _EnvironmentVariable(
    "QCFLOW_DATABRICKS_ENDPOINT_HTTP_RETRY_TIMEOUT", int, 500
)

#: Specifies the number of connection pools to cache in urllib3. This environment variable sets the
#: `pool_connections` parameter in the `requests.adapters.HTTPAdapter` constructor. By adjusting
#: this variable, users can enhance the concurrency of HTTP requests made by QCFlow.
QCFLOW_HTTP_POOL_CONNECTIONS = _EnvironmentVariable("QCFLOW_HTTP_POOL_CONNECTIONS", int, 10)

#: Specifies the maximum number of connections to keep in the HTTP connection pool. This environment
#: variable sets the `pool_maxsize` parameter in the `requests.adapters.HTTPAdapter` constructor.
#: By adjusting this variable, users can enhance the concurrency of HTTP requests made by QCFlow.
QCFLOW_HTTP_POOL_MAXSIZE = _EnvironmentVariable("QCFLOW_HTTP_POOL_MAXSIZE", int, 10)

#: Enable Unity Catalog integration for QCFlow AI Gateway.
#: (default: ``False``)
QCFLOW_ENABLE_UC_FUNCTIONS = _BooleanEnvironmentVariable("QCFLOW_ENABLE_UC_FUNCTIONS", False)

#: Specifies the length of time in seconds for the asynchronous logging thread to wait before
#: logging a batch.
QCFLOW_ASYNC_LOGGING_BUFFERING_SECONDS = _EnvironmentVariable(
    "QCFLOW_ASYNC_LOGGING_BUFFERING_SECONDS", int, None
)

#: Whether to enable Databricks SDK. If true, QCFlow uses databricks-sdk to send HTTP requests
#: to Databricks endpoint, otherwise QCFlow uses ``requests`` library to send HTTP requests
#: to Databricks endpoint. Note that if you want to use OAuth authentication, you have to
#: set this environment variable to true.
#: (default: ``True``)
QCFLOW_ENABLE_DB_SDK = _BooleanEnvironmentVariable("QCFLOW_ENABLE_DB_SDK", True)

#: A flag that's set to 'true' in the child process for capturing modules.
_QCFLOW_IN_CAPTURE_MODULE_PROCESS = _BooleanEnvironmentVariable(
    "QCFLOW_IN_CAPTURE_MODULE_PROCESS", False
)

#: Use DatabricksSDKModelsArtifactRepository when registering and loading models to and from
#: Databricks UC. This is required for SEG(Secure Egress Gateway) enabled workspaces and helps
#: eliminate models exfiltration risk associated with temporary scoped token generation used in
#: existing model artifact repo classes.
QCFLOW_USE_DATABRICKS_SDK_MODEL_ARTIFACTS_REPO_FOR_UC = _BooleanEnvironmentVariable(
    "QCFLOW_USE_DATABRICKS_SDK_MODEL_ARTIFACTS_REPO_FOR_UC", False
)

# Specifies the model environment archive file downloading path when using
# ``qcflow.pyfunc.spark_udf``. (default: ``None``)
QCFLOW_MODEL_ENV_DOWNLOADING_TEMP_DIR = _EnvironmentVariable(
    "QCFLOW_MODEL_ENV_DOWNLOADING_TEMP_DIR", str, None
)

# Specifies whether to log environment variable names used during model logging.
QCFLOW_RECORD_ENV_VARS_IN_MODEL_LOGGING = _BooleanEnvironmentVariable(
    "QCFLOW_RECORD_ENV_VARS_IN_MODEL_LOGGING", True
)

# Specifies whether to convert a {"messages": [{"role": "...", "content": "..."}]} input
# to a List[BaseMessage] object when invoking a PyFunc model saved with langchain flavor.
# This takes precedence over the default behavior of trying such conversion if the model
# is not an AgentExecutor and the input schema doesn't contain a 'messages' field.
QCFLOW_CONVERT_MESSAGES_DICT_FOR_LANGCHAIN = _BooleanEnvironmentVariable(
    "QCFLOW_CONVERT_MESSAGES_DICT_FOR_LANGCHAIN", None
)
