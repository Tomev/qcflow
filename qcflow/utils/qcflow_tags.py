"""
File containing all of the run tags in the qcflow. namespace.

See the System Tags section in the QCFlow Tracking documentation for information on the
meaning of these tags.
"""

QCFLOW_EXPERIMENT_SOURCE_ID = "qcflow.experiment.sourceId"
QCFLOW_EXPERIMENT_SOURCE_TYPE = "qcflow.experiment.sourceType"
QCFLOW_RUN_NAME = "qcflow.runName"
QCFLOW_RUN_NOTE = "qcflow.note.content"
QCFLOW_PARENT_RUN_ID = "qcflow.parentRunId"
QCFLOW_ARTIFACT_LOCATION = "qcflow.artifactLocation"
QCFLOW_USER = "qcflow.user"
QCFLOW_SOURCE_TYPE = "qcflow.source.type"
QCFLOW_RECIPE_TEMPLATE_NAME = "qcflow.pipeline.template.name"
QCFLOW_RECIPE_STEP_NAME = "qcflow.pipeline.step.name"
QCFLOW_RECIPE_PROFILE_NAME = "qcflow.pipeline.profile.name"
QCFLOW_SOURCE_NAME = "qcflow.source.name"
QCFLOW_GIT_COMMIT = "qcflow.source.git.commit"
QCFLOW_GIT_BRANCH = "qcflow.source.git.branch"
QCFLOW_GIT_REPO_URL = "qcflow.source.git.repoURL"
QCFLOW_LOGGED_MODELS = "qcflow.log-model.history"
QCFLOW_PROJECT_ENV = "qcflow.project.env"
QCFLOW_PROJECT_ENTRY_POINT = "qcflow.project.entryPoint"
QCFLOW_DOCKER_IMAGE_URI = "qcflow.docker.image.uri"
QCFLOW_DOCKER_IMAGE_ID = "qcflow.docker.image.id"
# Indicates that an QCFlow run was created by an autologging integration
QCFLOW_AUTOLOGGING = "qcflow.autologging"
# Indicates the artifacts type and path that are logged
QCFLOW_LOGGED_ARTIFACTS = "qcflow.loggedArtifacts"
QCFLOW_LOGGED_IMAGES = "qcflow.loggedImages"
QCFLOW_RUN_SOURCE_TYPE = "qcflow.runSourceType"

QCFLOW_DATABRICKS_NOTEBOOK_ID = "qcflow.databricks.notebookID"
QCFLOW_DATABRICKS_NOTEBOOK_PATH = "qcflow.databricks.notebookPath"
QCFLOW_DATABRICKS_WEBAPP_URL = "qcflow.databricks.webappURL"
QCFLOW_DATABRICKS_RUN_URL = "qcflow.databricks.runURL"
QCFLOW_DATABRICKS_CLUSTER_ID = "qcflow.databricks.cluster.id"
QCFLOW_DATABRICKS_WORKSPACE_URL = "qcflow.databricks.workspaceURL"
QCFLOW_DATABRICKS_WORKSPACE_ID = "qcflow.databricks.workspaceID"
# The unique ID of a command execution in a Databricks notebook
QCFLOW_DATABRICKS_NOTEBOOK_COMMAND_ID = "qcflow.databricks.notebook.commandID"
# The SHELL_JOB_ID and SHELL_JOB_RUN_ID tags are used for tracking the
# Databricks Job ID and Databricks Job Run ID associated with an QCFlow Project run
QCFLOW_DATABRICKS_SHELL_JOB_ID = "qcflow.databricks.shellJobID"
QCFLOW_DATABRICKS_SHELL_JOB_RUN_ID = "qcflow.databricks.shellJobRunID"
# The JOB_ID, JOB_RUN_ID, and JOB_TYPE tags are used for automatically recording Job information
# when QCFlow Tracking APIs are used within a Databricks Job
QCFLOW_DATABRICKS_JOB_ID = "qcflow.databricks.jobID"
QCFLOW_DATABRICKS_JOB_RUN_ID = "qcflow.databricks.jobRunID"
# Here QCFLOW_DATABRICKS_JOB_TYPE means the job task type and QCFLOW_DATABRICKS_JOB_TYPE_INFO
# implies the job type which could be normal, ephemeral, etc.
QCFLOW_DATABRICKS_JOB_TYPE = "qcflow.databricks.jobType"
QCFLOW_DATABRICKS_JOB_TYPE_INFO = "qcflow.databricks.jobTypeInfo"
# For QCFlow Repo Lineage tracking
QCFLOW_DATABRICKS_GIT_REPO_URL = "qcflow.databricks.gitRepoUrl"
QCFLOW_DATABRICKS_GIT_REPO_COMMIT = "qcflow.databricks.gitRepoCommit"
QCFLOW_DATABRICKS_GIT_REPO_PROVIDER = "qcflow.databricks.gitRepoProvider"
QCFLOW_DATABRICKS_GIT_REPO_RELATIVE_PATH = "qcflow.databricks.gitRepoRelativePath"
QCFLOW_DATABRICKS_GIT_REPO_REFERENCE = "qcflow.databricks.gitRepoReference"
QCFLOW_DATABRICKS_GIT_REPO_REFERENCE_TYPE = "qcflow.databricks.gitRepoReferenceType"
QCFLOW_DATABRICKS_GIT_REPO_STATUS = "qcflow.databricks.gitRepoStatus"

# For QCFlow Dataset tracking
QCFLOW_DATASET_CONTEXT = "qcflow.data.context"

QCFLOW_PROJECT_BACKEND = "qcflow.project.backend"

# The following legacy tags are deprecated and will be removed by QCFlow 1.0.
LEGACY_QCFLOW_GIT_BRANCH_NAME = "qcflow.gitBranchName"  # Replaced with qcflow.source.git.branch
LEGACY_QCFLOW_GIT_REPO_URL = "qcflow.gitRepoURL"  # Replaced with qcflow.source.git.repoURL

QCFLOW_EXPERIMENT_PRIMARY_METRIC_NAME = "qcflow.experiment.primaryMetric.name"
QCFLOW_EXPERIMENT_PRIMARY_METRIC_GREATER_IS_BETTER = (
    "qcflow.experiment.primaryMetric.greaterIsBetter"
)

# For automatic model checkpointing
LATEST_CHECKPOINT_ARTIFACT_TAG_KEY = "qcflow.latest_checkpoint_artifact"

# A set of tags that cannot be updated by the user
IMMUTABLE_TAGS = {QCFLOW_USER, QCFLOW_ARTIFACT_LOCATION}

# The list of tags generated from resolve_tags() that are required for tracing UI
TRACE_RESOLVE_TAGS_ALLOWLIST = (
    QCFLOW_DATABRICKS_NOTEBOOK_COMMAND_ID,
    QCFLOW_DATABRICKS_NOTEBOOK_ID,
    QCFLOW_DATABRICKS_NOTEBOOK_PATH,
    QCFLOW_DATABRICKS_WEBAPP_URL,
    QCFLOW_DATABRICKS_WORKSPACE_ID,
    QCFLOW_DATABRICKS_WORKSPACE_URL,
    QCFLOW_SOURCE_NAME,
    QCFLOW_SOURCE_TYPE,
    QCFLOW_USER,
)


def _get_run_name_from_tags(tags):
    for tag in tags:
        if tag.key == QCFLOW_RUN_NAME:
            return tag.value
