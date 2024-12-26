"""
Internal module implementing the fluent API, allowing management of an active
QCFlow run. This module is exposed to users at the top-level :py:mod:`qcflow` module.
"""

import atexit
import contextlib
import importlib
import inspect
import logging
import os
import threading
from copy import deepcopy
from typing import TYPE_CHECKING, Any, Optional, Union

import qcflow
from qcflow.data.dataset import Dataset
from qcflow.entities import (
    DatasetInput,
    Experiment,
    InputTag,
    Metric,
    Param,
    Run,
    RunStatus,
    RunTag,
    ViewType,
)
from qcflow.entities.lifecycle_stage import LifecycleStage
from qcflow.environment_variables import (
    QCFLOW_ENABLE_ASYNC_LOGGING,
    QCFLOW_ENABLE_SYSTEM_METRICS_LOGGING,
    QCFLOW_EXPERIMENT_ID,
    QCFLOW_EXPERIMENT_NAME,
    QCFLOW_RUN_ID,
)
from qcflow.exceptions import QCFlowException
from qcflow.protos.databricks_pb2 import (
    INVALID_PARAMETER_VALUE,
    RESOURCE_DOES_NOT_EXIST,
)
from qcflow.store.tracking import SEARCH_MAX_RESULTS_DEFAULT
from qcflow.tracing.provider import _get_trace_exporter
from qcflow.tracking import _get_artifact_repo, _get_store, artifact_utils
from qcflow.tracking.client import QCFlowClient
from qcflow.tracking.context import registry as context_registry
from qcflow.tracking.default_experiment import registry as default_experiment_registry
from qcflow.utils import get_results_from_paginated_fn
from qcflow.utils.annotations import experimental
from qcflow.utils.async_logging.run_operations import RunOperations
from qcflow.utils.autologging_utils import (
    AUTOLOGGING_CONF_KEY_IS_GLOBALLY_CONFIGURED,
    AUTOLOGGING_INTEGRATIONS,
    autologging_conf_lock,
    autologging_integration,
    autologging_is_disabled,
    is_testing,
)
from qcflow.utils.databricks_utils import is_in_databricks_runtime
from qcflow.utils.import_hooks import register_post_import_hook
from qcflow.utils.qcflow_tags import (
    QCFLOW_DATASET_CONTEXT,
    QCFLOW_EXPERIMENT_PRIMARY_METRIC_GREATER_IS_BETTER,
    QCFLOW_EXPERIMENT_PRIMARY_METRIC_NAME,
    QCFLOW_PARENT_RUN_ID,
    QCFLOW_RUN_NAME,
    QCFLOW_RUN_NOTE,
)
from qcflow.utils.thread_utils import ThreadLocalVariable
from qcflow.utils.time import get_current_time_millis
from qcflow.utils.validation import _validate_experiment_id_type, _validate_run_id

if TYPE_CHECKING:
    import matplotlib
    import matplotlib.figure
    import numpy
    import pandas
    import PIL
    import plotly


_active_experiment_id = None

SEARCH_MAX_RESULTS_PANDAS = 100000
NUM_RUNS_PER_PAGE_PANDAS = 10000

_logger = logging.getLogger(__name__)


run_id_to_system_metrics_monitor = {}


_active_run_stack = ThreadLocalVariable(default_factory=lambda: [])

_last_active_run_id = ThreadLocalVariable(default_factory=lambda: None)

_experiment_lock = threading.Lock()


def set_experiment(
    experiment_name: Optional[str] = None, experiment_id: Optional[str] = None
) -> Experiment:
    """
    Set the given experiment as the active experiment. The experiment must either be specified by
    name via `experiment_name` or by ID via `experiment_id`. The experiment name and ID cannot
    both be specified.

    .. note::
        If the experiment being set by name does not exist, a new experiment will be
        created with the given name. After the experiment has been created, it will be set
        as the active experiment. On certain platforms, such as Databricks, the experiment name
        must be an absolute path, e.g. ``"/Users/<username>/my-experiment"``.

    Args:
        experiment_name: Case sensitive name of the experiment to be activated.
        experiment_id: ID of the experiment to be activated. If an experiment with this ID
            does not exist, an exception is thrown.

    Returns:
        An instance of :py:class:`qcflow.entities.Experiment` representing the new active
        experiment.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        # Set an experiment name, which must be unique and case-sensitive.
        experiment = qcflow.set_experiment("Social NLP Experiments")
        # Get Experiment Details
        print(f"Experiment_id: {experiment.experiment_id}")
        print(f"Artifact Location: {experiment.artifact_location}")
        print(f"Tags: {experiment.tags}")
        print(f"Lifecycle_stage: {experiment.lifecycle_stage}")

    .. code-block:: text
        :caption: Output

        Experiment_id: 1
        Artifact Location: file:///.../mlruns/1
        Tags: {}
        Lifecycle_stage: active
    """
    if (experiment_name is not None and experiment_id is not None) or (
        experiment_name is None and experiment_id is None
    ):
        raise QCFlowException(
            message="Must specify exactly one of: `experiment_id` or `experiment_name`.",
            error_code=INVALID_PARAMETER_VALUE,
        )

    client = QCFlowClient()

    with _experiment_lock:
        if experiment_id is None:
            experiment = client.get_experiment_by_name(experiment_name)
            if not experiment:
                try:
                    experiment_id = client.create_experiment(experiment_name)
                    _logger.info(
                        "Experiment with name '%s' does not exist. Creating a new experiment.",
                        experiment_name,
                    )
                except QCFlowException as e:
                    if e.error_code == "RESOURCE_ALREADY_EXISTS":
                        # NB: If two simultaneous processes attempt to set the same experiment
                        # simultaneously, a race condition may be encountered here wherein
                        # experiment creation fails
                        return client.get_experiment_by_name(experiment_name)

                experiment = client.get_experiment(experiment_id)
        else:
            experiment = client.get_experiment(experiment_id)
            if experiment is None:
                raise QCFlowException(
                    message=f"Experiment with ID '{experiment_id}' does not exist.",
                    error_code=RESOURCE_DOES_NOT_EXIST,
                )

        if experiment.lifecycle_stage != LifecycleStage.ACTIVE:
            raise QCFlowException(
                message=(
                    f"Cannot set a deleted experiment {experiment.name!r} as the active"
                    " experiment. "
                    "You can restore the experiment, or permanently delete the "
                    "experiment to create a new one."
                ),
                error_code=INVALID_PARAMETER_VALUE,
            )

    global _active_experiment_id
    _active_experiment_id = experiment.experiment_id

    # Set 'QCFLOW_EXPERIMENT_ID' environment variable
    # so that subprocess can inherit it.
    QCFLOW_EXPERIMENT_ID.set(_active_experiment_id)

    return experiment


def _set_experiment_primary_metric(
    experiment_id: str, primary_metric: str, greater_is_better: bool
):
    client = QCFlowClient()
    client.set_experiment_tag(experiment_id, QCFLOW_EXPERIMENT_PRIMARY_METRIC_NAME, primary_metric)
    client.set_experiment_tag(
        experiment_id, QCFLOW_EXPERIMENT_PRIMARY_METRIC_GREATER_IS_BETTER, str(greater_is_better)
    )


class ActiveRun(Run):
    """Wrapper around :py:class:`qcflow.entities.Run` to enable using Python ``with`` syntax."""

    def __init__(self, run):
        Run.__init__(self, run.info, run.data)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        active_run_stack = _active_run_stack.get()

        # Check if the run is still active. We check based on ID instead of
        # using referential equality, because some tools (e.g. AutoML) may
        # stop a run and start it again with the same ID to restore session state
        if any(r.info.run_id == self.info.run_id for r in active_run_stack):
            status = RunStatus.FINISHED if exc_type is None else RunStatus.FAILED
            end_run(RunStatus.to_string(status))

        return exc_type is None


def start_run(
    run_id: Optional[str] = None,
    experiment_id: Optional[str] = None,
    run_name: Optional[str] = None,
    nested: bool = False,
    parent_run_id: Optional[str] = None,
    tags: Optional[dict[str, Any]] = None,
    description: Optional[str] = None,
    log_system_metrics: Optional[bool] = None,
) -> ActiveRun:
    """
    Start a new QCFlow run, setting it as the active run under which metrics and parameters
    will be logged. The return value can be used as a context manager within a ``with`` block;
    otherwise, you must call ``end_run()`` to terminate the current run.

    If you pass a ``run_id`` or the ``QCFLOW_RUN_ID`` environment variable is set,
    ``start_run`` attempts to resume a run with the specified run ID and
    other parameters are ignored. ``run_id`` takes precedence over ``QCFLOW_RUN_ID``.

    If resuming an existing run, the run status is set to ``RunStatus.RUNNING``.

    QCFlow sets a variety of default tags on the run, as defined in
    :ref:`QCFlow system tags <system_tags>`.

    Args:
        run_id: If specified, get the run with the specified UUID and log parameters
            and metrics under that run. The run's end time is unset and its status
            is set to running, but the run's other attributes (``source_version``,
            ``source_type``, etc.) are not changed.
        experiment_id: ID of the experiment under which to create the current run (applicable
            only when ``run_id`` is not specified). If ``experiment_id`` argument
            is unspecified, will look for valid experiment in the following order:
            activated using ``set_experiment``, ``QCFLOW_EXPERIMENT_NAME``
            environment variable, ``QCFLOW_EXPERIMENT_ID`` environment variable,
            or the default experiment as defined by the tracking server.
        run_name: Name of new run. Used only when ``run_id`` is unspecified. If a new run is
            created and ``run_name`` is not specified, a random name will be generated for the run.
        nested: Controls whether run is nested in parent run. ``True`` creates a nested run.
        parent_run_id: If specified, the current run will be nested under the the run with
            the specified UUID. The parent run must be in the ACTIVE state.
        tags: An optional dictionary of string keys and values to set as tags on the run.
            If a run is being resumed, these tags are set on the resumed run. If a new run is
            being created, these tags are set on the new run.
        description: An optional string that populates the description box of the run.
            If a run is being resumed, the description is set on the resumed run.
            If a new run is being created, the description is set on the new run.
        log_system_metrics: bool, defaults to None. If True, system metrics will be logged
            to QCFlow, e.g., cpu/gpu utilization. If None, we will check environment variable
            `QCFLOW_ENABLE_SYSTEM_METRICS_LOGGING` to determine whether to log system metrics.
            System metrics logging is an experimental feature in QCFlow 2.8 and subject to change.

    Returns:
        :py:class:`qcflow.ActiveRun` object that acts as a context manager wrapping the
        run's state.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        # Create nested runs
        experiment_id = qcflow.create_experiment("experiment1")
        with qcflow.start_run(
            run_name="PARENT_RUN",
            experiment_id=experiment_id,
            tags={"version": "v1", "priority": "P1"},
            description="parent",
        ) as parent_run:
            qcflow.log_param("parent", "yes")
            with qcflow.start_run(
                run_name="CHILD_RUN",
                experiment_id=experiment_id,
                description="child",
                nested=True,
            ) as child_run:
                qcflow.log_param("child", "yes")
        print("parent run:")
        print(f"run_id: {parent_run.info.run_id}")
        print("description: {}".format(parent_run.data.tags.get("qcflow.note.content")))
        print("version tag value: {}".format(parent_run.data.tags.get("version")))
        print("priority tag value: {}".format(parent_run.data.tags.get("priority")))
        print("--")

        # Search all child runs with a parent id
        query = f"tags.qcflow.parentRunId = '{parent_run.info.run_id}'"
        results = qcflow.search_runs(experiment_ids=[experiment_id], filter_string=query)
        print("child runs:")
        print(results[["run_id", "params.child", "tags.qcflow.runName"]])

        # Create a nested run under the existing parent run
        with qcflow.start_run(
            run_name="NEW_CHILD_RUN",
            experiment_id=experiment_id,
            description="new child",
            parent_run_id=parent_run.info.run_id,
        ) as child_run:
            qcflow.log_param("new-child", "yes")

    .. code-block:: text
        :caption: Output

        parent run:
        run_id: 8979459433a24a52ab3be87a229a9cdf
        description: starting a parent for experiment 7
        version tag value: v1
        priority tag value: P1
        --
        child runs:
                                     run_id params.child tags.qcflow.runName
        0  7d175204675e40328e46d9a6a5a7ee6a          yes           CHILD_RUN
    """
    active_run_stack = _active_run_stack.get()
    _validate_experiment_id_type(experiment_id)
    # back compat for int experiment_id
    experiment_id = str(experiment_id) if isinstance(experiment_id, int) else experiment_id
    if len(active_run_stack) > 0 and not nested:
        raise Exception(
            (
                "Run with UUID {} is already active. To start a new run, first end the "
                + "current run with qcflow.end_run(). To start a nested "
                + "run, call start_run with nested=True"
            ).format(active_run_stack[0].info.run_id)
        )
    client = QCFlowClient()
    if run_id:
        existing_run_id = run_id
    elif run_id := QCFLOW_RUN_ID.get():
        existing_run_id = run_id
        del os.environ[QCFLOW_RUN_ID.name]
    else:
        existing_run_id = None
    if existing_run_id:
        _validate_run_id(existing_run_id)
        active_run_obj = client.get_run(existing_run_id)
        # Check to see if experiment_id from environment matches experiment_id from set_experiment()
        if (
            _active_experiment_id is not None
            and _active_experiment_id != active_run_obj.info.experiment_id
        ):
            raise QCFlowException(
                f"Cannot start run with ID {existing_run_id} because active run ID "
                "does not match environment run ID. Make sure --experiment-name "
                "or --experiment-id matches experiment set with "
                "set_experiment(), or just use command-line arguments"
            )
        # Check if the current run has been deleted.
        if active_run_obj.info.lifecycle_stage == LifecycleStage.DELETED:
            raise QCFlowException(
                f"Cannot start run with ID {existing_run_id} because it is in the deleted state."
            )
        # Use previous `end_time` because a value is required for `update_run_info`.
        end_time = active_run_obj.info.end_time
        _get_store().update_run_info(
            existing_run_id, run_status=RunStatus.RUNNING, end_time=end_time, run_name=None
        )
        tags = tags or {}
        if description:
            if QCFLOW_RUN_NOTE in tags:
                raise QCFlowException(
                    f"Description is already set via the tag {QCFLOW_RUN_NOTE} in tags."
                    f"Remove the key {QCFLOW_RUN_NOTE} from the tags or omit the description.",
                    error_code=INVALID_PARAMETER_VALUE,
                )
            tags[QCFLOW_RUN_NOTE] = description

        if tags:
            client.log_batch(
                run_id=existing_run_id,
                tags=[RunTag(key, str(value)) for key, value in tags.items()],
            )
        active_run_obj = client.get_run(existing_run_id)
    else:
        if parent_run_id:
            _validate_run_id(parent_run_id)
            # Make sure parent_run_id matches the current run id, if there is an active run
            if len(active_run_stack) > 0 and parent_run_id != active_run_stack[-1].info.run_id:
                current_run_id = active_run_stack[-1].info.run_id
                raise QCFlowException(
                    f"Current run with UUID {current_run_id} does not match the specified "
                    f"parent_run_id {parent_run_id}. To start a new nested run under "
                    f"the parent run with UUID {current_run_id}, first end the current run "
                    "with qcflow.end_run()."
                )
            parent_run_obj = client.get_run(parent_run_id)
            # Check if the specified parent_run has been deleted.
            if parent_run_obj.info.lifecycle_stage == LifecycleStage.DELETED:
                raise QCFlowException(
                    f"Cannot start run under parent run with ID {parent_run_id} "
                    f"because it is in the deleted state."
                )
        else:
            parent_run_id = active_run_stack[-1].info.run_id if len(active_run_stack) > 0 else None

        exp_id_for_run = experiment_id if experiment_id is not None else _get_experiment_id()

        user_specified_tags = deepcopy(tags) or {}
        if description:
            if QCFLOW_RUN_NOTE in user_specified_tags:
                raise QCFlowException(
                    f"Description is already set via the tag {QCFLOW_RUN_NOTE} in tags."
                    f"Remove the key {QCFLOW_RUN_NOTE} from the tags or omit the description.",
                    error_code=INVALID_PARAMETER_VALUE,
                )
            user_specified_tags[QCFLOW_RUN_NOTE] = description
        if parent_run_id is not None:
            user_specified_tags[QCFLOW_PARENT_RUN_ID] = parent_run_id
        if run_name:
            user_specified_tags[QCFLOW_RUN_NAME] = run_name

        resolved_tags = context_registry.resolve_tags(user_specified_tags)

        active_run_obj = client.create_run(
            experiment_id=exp_id_for_run,
            tags=resolved_tags,
            run_name=run_name,
        )

    if log_system_metrics is None:
        # If `log_system_metrics` is not specified, we will check environment variable.
        log_system_metrics = QCFLOW_ENABLE_SYSTEM_METRICS_LOGGING.get()

    if log_system_metrics:
        if importlib.util.find_spec("psutil") is None:
            raise QCFlowException(
                "Failed to start system metrics monitoring as package `psutil` is not installed. "
                "Please run `pip install psutil` to resolve the issue, otherwise you can disable "
                "system metrics logging by passing `log_system_metrics=False` to "
                "`qcflow.start_run()` or calling `qcflow.disable_system_metrics_logging`."
            )
        try:
            from qcflow.system_metrics.system_metrics_monitor import SystemMetricsMonitor

            system_monitor = SystemMetricsMonitor(
                active_run_obj.info.run_id,
                resume_logging=existing_run_id is not None,
            )
            run_id_to_system_metrics_monitor[active_run_obj.info.run_id] = system_monitor
            system_monitor.start()
        except Exception as e:
            _logger.error(f"Failed to start system metrics monitoring: {e}.")

    active_run_stack.append(ActiveRun(active_run_obj))
    return active_run_stack[-1]


def end_run(status: str = RunStatus.to_string(RunStatus.FINISHED)) -> None:
    """
    End an active QCFlow run (if there is one).

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        # Start run and get status
        qcflow.start_run()
        run = qcflow.active_run()
        print(f"run_id: {run.info.run_id}; status: {run.info.status}")

        # End run and get status
        qcflow.end_run()
        run = qcflow.get_run(run.info.run_id)
        print(f"run_id: {run.info.run_id}; status: {run.info.status}")
        print("--")

        # Check for any active runs
        print(f"Active run: {qcflow.active_run()}")

    .. code-block:: text
        :caption: Output

        run_id: b47ee4563368419880b44ad8535f6371; status: RUNNING
        run_id: b47ee4563368419880b44ad8535f6371; status: FINISHED
        --
        Active run: None
    """
    active_run_stack = _active_run_stack.get()
    if len(active_run_stack) > 0:
        # Clear out the global existing run environment variable as well.
        QCFLOW_RUN_ID.unset()
        run = active_run_stack.pop()
        last_active_run_id = run.info.run_id
        _last_active_run_id.set(last_active_run_id)
        QCFlowClient().set_terminated(last_active_run_id, status)
        if last_active_run_id in run_id_to_system_metrics_monitor:
            system_metrics_monitor = run_id_to_system_metrics_monitor.pop(last_active_run_id)
            system_metrics_monitor.finish()


def _safe_end_run():
    with contextlib.suppress(Exception):
        end_run()


atexit.register(_safe_end_run)


def active_run() -> Optional[ActiveRun]:
    """
    Get the currently active ``Run``, or None if no such run exists.

    .. attention::
        This API is **thread-local** and returns only the active run in the current thread.
        If your application is multi-threaded and a run is started in a different thread,
        this API will not retrieve that run.

    **Note**: You cannot access currently-active run attributes
    (parameters, metrics, etc.) through the run returned by ``qcflow.active_run``. In order
    to access such attributes, use the :py:class:`qcflow.client.QCFlowClient` as follows:

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        qcflow.start_run()
        run = qcflow.active_run()
        print(f"Active run_id: {run.info.run_id}")
        qcflow.end_run()

    .. code-block:: text
        :caption: Output

        Active run_id: 6f252757005748708cd3aad75d1ff462
    """
    active_run_stack = _active_run_stack.get()
    return active_run_stack[-1] if len(active_run_stack) > 0 else None


def last_active_run() -> Optional[Run]:
    """Gets the most recent active run.

    Examples:

    .. code-block:: python
        :test:
        :caption: To retrieve the most recent autologged run:

        import qcflow

        from sklearn.model_selection import train_test_split
        from sklearn.datasets import load_diabetes
        from sklearn.ensemble import RandomForestRegressor

        qcflow.autolog()

        db = load_diabetes()
        X_train, X_test, y_train, y_test = train_test_split(db.data, db.target)

        # Create and train models.
        rf = RandomForestRegressor(n_estimators=100, max_depth=6, max_features=3)
        rf.fit(X_train, y_train)

        # Use the model to make predictions on the test dataset.
        predictions = rf.predict(X_test)
        autolog_run = qcflow.last_active_run()

    .. code-block:: python
        :test:
        :caption: To get the most recently active run that ended:

        import qcflow

        qcflow.start_run()
        qcflow.end_run()
        run = qcflow.last_active_run()

    .. code-block:: python
        :test:
        :caption: To retrieve the currently active run:

        import qcflow

        qcflow.start_run()
        run = qcflow.last_active_run()
        qcflow.end_run()

    Returns:
        The active run (this is equivalent to ``qcflow.active_run()``) if one exists.
        Otherwise, the last run started from the current Python process that reached
        a terminal status (i.e. FINISHED, FAILED, or KILLED).
    """
    _active_run = active_run()
    if _active_run is not None:
        return _active_run

    last_active_run_id = _last_active_run_id.get()
    if last_active_run_id is None:
        return None
    return get_run(last_active_run_id)


def _get_latest_active_run():
    """
    Get active run from global context by checking all threads. The `qcflow.active_run` API
    only returns active run from current thread. This API is useful for the case where one
    needs to get a run started from a separate thread.
    """
    all_active_runs = [
        run for run_stack in _active_run_stack.get_all_thread_values().values() for run in run_stack
    ]
    if all_active_runs:
        return max(all_active_runs, key=lambda run: run.info.start_time)
    return None


def get_run(run_id: str) -> Run:
    """
    Fetch the run from backend store. The resulting Run contains a collection of run metadata --
    RunInfo as well as a collection of run parameters, tags, and metrics -- RunData. It also
    contains a collection of run inputs (experimental), including information about datasets used by
    the run -- RunInputs. In the case where multiple metrics with the same key are logged for the
    run, the RunData contains the most recently logged value at the largest step for each metric.

    Args:
        run_id: Unique identifier for the run.

    Returns:
        A single Run object, if the run exists. Otherwise, raises an exception.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        with qcflow.start_run() as run:
            qcflow.log_param("p", 0)
        run_id = run.info.run_id
        print(
            f"run_id: {run_id}; lifecycle_stage: {qcflow.get_run(run_id).info.lifecycle_stage}"
        )

    .. code-block:: text
        :caption: Output

        run_id: 7472befefc754e388e8e922824a0cca5; lifecycle_stage: active
    """
    return QCFlowClient().get_run(run_id)


def get_parent_run(run_id: str) -> Optional[Run]:
    """Gets the parent run for the given run id if one exists.

    Args:
        run_id: Unique identifier for the child run.

    Returns:
        A single :py:class:`qcflow.entities.Run` object, if the parent run exists. Otherwise,
        returns None.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        # Create nested runs
        with qcflow.start_run():
            with qcflow.start_run(nested=True) as child_run:
                child_run_id = child_run.info.run_id

        parent_run = qcflow.get_parent_run(child_run_id)

        print(f"child_run_id: {child_run_id}")
        print(f"parent_run_id: {parent_run.info.run_id}")

    .. code-block:: text
        :caption: Output

        child_run_id: 7d175204675e40328e46d9a6a5a7ee6a
        parent_run_id: 8979459433a24a52ab3be87a229a9cdf
    """
    return QCFlowClient().get_parent_run(run_id)


def log_param(key: str, value: Any, synchronous: Optional[bool] = None) -> Any:
    """
    Log a parameter (e.g. model hyperparameter) under the current run. If no run is active,
    this method will create a new active run.

    Args:
        key: Parameter name. This string may only contain alphanumerics, underscores (_), dashes
            (-), periods (.), spaces ( ), and slashes (/). All backend stores support keys up to
            length 250, but some may support larger keys.
        value: Parameter value, but will be string-ified if not. All built-in backend stores support
            values up to length 6000, but some may support larger values.
        synchronous: *Experimental* If True, blocks until the parameter is logged successfully. If
            False, logs the parameter asynchronously and returns a future representing the logging
            operation. If None, read from environment variable `QCFLOW_ENABLE_ASYNC_LOGGING`,
            which defaults to False if not set.

    Returns:
        When `synchronous=True`, returns parameter value. When `synchronous=False`, returns an
        :py:class:`qcflow.utils.async_logging.run_operations.RunOperations` instance that represents
        future for logging operation.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        with qcflow.start_run():
            value = qcflow.log_param("learning_rate", 0.01)
            assert value == 0.01
            value = qcflow.log_param("learning_rate", 0.02, synchronous=False)
    """
    run_id = _get_or_start_run().info.run_id
    synchronous = synchronous if synchronous is not None else not QCFLOW_ENABLE_ASYNC_LOGGING.get()
    return QCFlowClient().log_param(run_id, key, value, synchronous=synchronous)


def flush_async_logging() -> None:
    """Flush all pending async logging."""
    _get_store().flush_async_logging()


def _shut_down_async_logging() -> None:
    """Shutdown the async logging and flush all pending data."""
    _get_store().shut_down_async_logging()


def flush_artifact_async_logging() -> None:
    """Flush all pending artifact async logging."""
    run_id = _get_or_start_run().info.run_id
    _artifact_repo = _get_artifact_repo(run_id)
    if _artifact_repo:
        _artifact_repo.flush_async_logging()


def flush_trace_async_logging(terminate=False) -> None:
    """
    Flush all pending trace async logging.

    Args:
        terminate: If True, shut down the logging threads after flushing.
    """
    try:
        _get_trace_exporter()._async_queue.flush(terminate=terminate)
    except Exception as e:
        _logger.error(f"Failed to flush trace async logging: {e}")


def set_experiment_tag(key: str, value: Any) -> None:
    """
    Set a tag on the current experiment. Value is converted to a string.

    Args:
        key: Tag name. This string may only contain alphanumerics, underscores (_), dashes (-),
            periods (.), spaces ( ), and slashes (/). All backend stores will support keys up to
            length 250, but some may support larger keys.
        value: Tag value, but will be string-ified if not. All backend stores will support values
            up to length 5000, but some may support larger values.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        with qcflow.start_run():
            qcflow.set_experiment_tag("release.version", "2.2.0")
    """
    experiment_id = _get_experiment_id()
    QCFlowClient().set_experiment_tag(experiment_id, key, value)


def set_tag(key: str, value: Any, synchronous: Optional[bool] = None) -> Optional[RunOperations]:
    """
    Set a tag under the current run. If no run is active, this method will create a new active
    run.

    Args:
        key: Tag name. This string may only contain alphanumerics, underscores (_), dashes (-),
            periods (.), spaces ( ), and slashes (/). All backend stores will support keys up to
            length 250, but some may support larger keys.
        value: Tag value, but will be string-ified if not. All backend stores will support values
            up to length 5000, but some may support larger values.
        synchronous: *Experimental* If True, blocks until the tag is logged successfully. If False,
            logs the tag asynchronously and returns a future representing the logging operation.
            If None, read from environment variable `QCFLOW_ENABLE_ASYNC_LOGGING`, which
            defaults to False if not set.

    Returns:
        When `synchronous=True`, returns None. When `synchronous=False`, returns an
        :py:class:`qcflow.utils.async_logging.run_operations.RunOperations` instance that
        represents future for logging operation.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        # Set a tag.
        with qcflow.start_run():
            qcflow.set_tag("release.version", "2.2.0")

        # Set a tag in async fashion.
        with qcflow.start_run():
            qcflow.set_tag("release.version", "2.2.1", synchronous=False)
    """
    run_id = _get_or_start_run().info.run_id
    synchronous = synchronous if synchronous is not None else not QCFLOW_ENABLE_ASYNC_LOGGING.get()
    return QCFlowClient().set_tag(run_id, key, value, synchronous=synchronous)


def delete_tag(key: str) -> None:
    """
    Delete a tag from a run. This is irreversible. If no run is active, this method
    will create a new active run.

    Args:
        key: Name of the tag

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        tags = {"engineering": "ML Platform", "engineering_remote": "ML Platform"}

        with qcflow.start_run() as run:
            qcflow.set_tags(tags)

        with qcflow.start_run(run_id=run.info.run_id):
            qcflow.delete_tag("engineering_remote")
    """
    run_id = _get_or_start_run().info.run_id
    QCFlowClient().delete_tag(run_id, key)


def log_metric(
    key: str,
    value: float,
    step: Optional[int] = None,
    synchronous: Optional[bool] = None,
    timestamp: Optional[int] = None,
    run_id: Optional[str] = None,
) -> Optional[RunOperations]:
    """
    Log a metric under the current run. If no run is active, this method will create
    a new active run.

    Args:
        key: Metric name. This string may only contain alphanumerics, underscores (_),
            dashes (-), periods (.), spaces ( ), and slashes (/).
            All backend stores will support keys up to length 250, but some may
            support larger keys.
        value: Metric value. Note that some special values such as +/- Infinity may be
            replaced by other values depending on the store. For example, the
            SQLAlchemy store replaces +/- Infinity with max / min float values.
            All backend stores will support values up to length 5000, but some
            may support larger values.
        step: Metric step. Defaults to zero if unspecified.
        synchronous: *Experimental* If True, blocks until the metric is logged
            successfully. If False, logs the metric asynchronously and
            returns a future representing the logging operation. If None, read from environment
            variable `QCFLOW_ENABLE_ASYNC_LOGGING`, which defaults to False if not set.
        timestamp: Time when this metric was calculated. Defaults to the current system time.
        run_id: If specified, log the metric to the specified run. If not specified, log the metric
            to the currently active run.

    Returns:
        When `synchronous=True`, returns None.
        When `synchronous=False`, returns `RunOperations` that represents future for
        logging operation.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        # Log a metric
        with qcflow.start_run():
            qcflow.log_metric("mse", 2500.00)

        # Log a metric in async fashion.
        with qcflow.start_run():
            qcflow.log_metric("mse", 2500.00, synchronous=False)
    """
    run_id = run_id or _get_or_start_run().info.run_id
    synchronous = synchronous if synchronous is not None else not QCFLOW_ENABLE_ASYNC_LOGGING.get()
    return QCFlowClient().log_metric(
        run_id,
        key,
        value,
        timestamp or get_current_time_millis(),
        step or 0,
        synchronous=synchronous,
    )


def log_metrics(
    metrics: dict[str, float],
    step: Optional[int] = None,
    synchronous: Optional[bool] = None,
    run_id: Optional[str] = None,
    timestamp: Optional[int] = None,
) -> Optional[RunOperations]:
    """
    Log multiple metrics for the current run. If no run is active, this method will create a new
    active run.

    Args:
        metrics: Dictionary of metric_name: String -> value: Float. Note that some special
            values such as +/- Infinity may be replaced by other values depending on
            the store. For example, sql based store may replace +/- Infinity with
            max / min float values.
        step: A single integer step at which to log the specified
            Metrics. If unspecified, each metric is logged at step zero.
        synchronous: *Experimental* If True, blocks until the metrics are logged
            successfully. If False, logs the metrics asynchronously and
            returns a future representing the logging operation. If None, read from environment
            variable `QCFLOW_ENABLE_ASYNC_LOGGING`, which defaults to False if not set.
        run_id: Run ID. If specified, log metrics to the specified run. If not specified, log
            metrics to the currently active run.
        timestamp: Time when these metrics were calculated. Defaults to the current system time.

    Returns:
        When `synchronous=True`, returns None. When `synchronous=False`, returns an
        :py:class:`qcflow.utils.async_logging.run_operations.RunOperations` instance that
        represents future for logging operation.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        metrics = {"mse": 2500.00, "rmse": 50.00}

        # Log a batch of metrics
        with qcflow.start_run():
            qcflow.log_metrics(metrics)

        # Log a batch of metrics in async fashion.
        with qcflow.start_run():
            qcflow.log_metrics(metrics, synchronous=False)
    """
    run_id = run_id or _get_or_start_run().info.run_id
    timestamp = timestamp or get_current_time_millis()
    metrics_arr = [Metric(key, value, timestamp, step or 0) for key, value in metrics.items()]
    synchronous = synchronous if synchronous is not None else not QCFLOW_ENABLE_ASYNC_LOGGING.get()
    return QCFlowClient().log_batch(
        run_id=run_id, metrics=metrics_arr, params=[], tags=[], synchronous=synchronous
    )


def log_params(
    params: dict[str, Any], synchronous: Optional[bool] = None, run_id: Optional[str] = None
) -> Optional[RunOperations]:
    """
    Log a batch of params for the current run. If no run is active, this method will create a
    new active run.

    Args:
        params: Dictionary of param_name: String -> value: (String, but will be string-ified if
            not)
        synchronous: *Experimental* If True, blocks until the parameters are logged
            successfully. If False, logs the parameters asynchronously and
            returns a future representing the logging operation. If None, read from environment
            variable `QCFLOW_ENABLE_ASYNC_LOGGING`, which defaults to False if not set.
        run_id: Run ID. If specified, log params to the specified run. If not specified, log
            params to the currently active run.

    Returns:
        When `synchronous=True`, returns None. When `synchronous=False`, returns an
        :py:class:`qcflow.utils.async_logging.run_operations.RunOperations` instance that
        represents future for logging operation.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        params = {"learning_rate": 0.01, "n_estimators": 10}

        # Log a batch of parameters
        with qcflow.start_run():
            qcflow.log_params(params)

        # Log a batch of parameters in async fashion.
        with qcflow.start_run():
            qcflow.log_params(params, synchronous=False)
    """
    run_id = run_id or _get_or_start_run().info.run_id
    params_arr = [Param(key, str(value)) for key, value in params.items()]
    synchronous = synchronous if synchronous is not None else not QCFLOW_ENABLE_ASYNC_LOGGING.get()
    return QCFlowClient().log_batch(
        run_id=run_id, metrics=[], params=params_arr, tags=[], synchronous=synchronous
    )


def log_input(
    dataset: Dataset, context: Optional[str] = None, tags: Optional[dict[str, str]] = None
) -> None:
    """
    Log a dataset used in the current run.

    Args:
        dataset: :py:class:`qcflow.data.dataset.Dataset` object to be logged.
        context: Context in which the dataset is used. For example: "training", "testing".
            This will be set as an input tag with key `qcflow.data.context`.
        tags: Tags to be associated with the dataset. Dictionary of tag_key -> tag_value.

    .. code-block:: python
        :test:
        :caption: Example

        import numpy as np
        import qcflow

        array = np.asarray([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
        dataset = qcflow.data.from_numpy(array, source="data.csv")

        # Log an input dataset used for training
        with qcflow.start_run():
            qcflow.log_input(dataset, context="training")
    """
    run_id = _get_or_start_run().info.run_id
    tags_to_log = []
    if tags:
        tags_to_log.extend([InputTag(key=key, value=value) for key, value in tags.items()])
    if context:
        tags_to_log.append(InputTag(key=QCFLOW_DATASET_CONTEXT, value=context))

    dataset_input = DatasetInput(dataset=dataset._to_qcflow_entity(), tags=tags_to_log)

    QCFlowClient().log_inputs(run_id=run_id, datasets=[dataset_input])


def set_experiment_tags(tags: dict[str, Any]) -> None:
    """
    Set tags for the current active experiment.

    Args:
        tags: Dictionary containing tag names and corresponding values.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        tags = {
            "engineering": "ML Platform",
            "release.candidate": "RC1",
            "release.version": "2.2.0",
        }

        # Set a batch of tags
        with qcflow.start_run():
            qcflow.set_experiment_tags(tags)
    """
    for key, value in tags.items():
        set_experiment_tag(key, value)


def set_tags(tags: dict[str, Any], synchronous: Optional[bool] = None) -> Optional[RunOperations]:
    """
    Log a batch of tags for the current run. If no run is active, this method will create a
    new active run.

    Args:
        tags: Dictionary of tag_name: String -> value: (String, but will be string-ified if
            not)
        synchronous: *Experimental* If True, blocks until tags are logged successfully. If False,
            logs tags asynchronously and returns a future representing the logging operation.
            If None, read from environment variable `QCFLOW_ENABLE_ASYNC_LOGGING`, which
            defaults to False if not set.

    Returns:
        When `synchronous=True`, returns None. When `synchronous=False`, returns an
        :py:class:`qcflow.utils.async_logging.run_operations.RunOperations` instance that
        represents future for logging operation.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        tags = {
            "engineering": "ML Platform",
            "release.candidate": "RC1",
            "release.version": "2.2.0",
        }

        # Set a batch of tags
        with qcflow.start_run():
            qcflow.set_tags(tags)

        # Set a batch of tags in async fashion.
        with qcflow.start_run():
            qcflow.set_tags(tags, synchronous=False)
    """
    run_id = _get_or_start_run().info.run_id
    tags_arr = [RunTag(key, str(value)) for key, value in tags.items()]
    synchronous = synchronous if synchronous is not None else not QCFLOW_ENABLE_ASYNC_LOGGING.get()
    return QCFlowClient().log_batch(
        run_id=run_id, metrics=[], params=[], tags=tags_arr, synchronous=synchronous
    )


def log_artifact(
    local_path: str, artifact_path: Optional[str] = None, run_id: Optional[str] = None
) -> None:
    """
    Log a local file or directory as an artifact of the currently active run. If no run is
    active, this method will create a new active run.

    Args:
        local_path: Path to the file to write.
        artifact_path: If provided, the directory in ``artifact_uri`` to write to.
        run_id: If specified, log the artifact to the specified run. If not specified, log the
            artifact to the currently active run.

    .. code-block:: python
        :test:
        :caption: Example

        import tempfile
        from pathlib import Path

        import qcflow

        # Create a features.txt artifact file
        features = "rooms, zipcode, median_price, school_rating, transport"
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir, "features.txt")
            path.write_text(features)
            # With artifact_path=None write features.txt under
            # root artifact_uri/artifacts directory
            with qcflow.start_run():
                qcflow.log_artifact(path)
    """
    run_id = run_id or _get_or_start_run().info.run_id
    QCFlowClient().log_artifact(run_id, local_path, artifact_path)


def log_artifacts(
    local_dir: str, artifact_path: Optional[str] = None, run_id: Optional[str] = None
) -> None:
    """
    Log all the contents of a local directory as artifacts of the run. If no run is active,
    this method will create a new active run.

    Args:
        local_dir: Path to the directory of files to write.
        artifact_path: If provided, the directory in ``artifact_uri`` to write to.
        run_id: If specified, log the artifacts to the specified run. If not specified, log the
            artifacts to the currently active run.

    .. code-block:: python
        :test:
        :caption: Example

        import json
        import tempfile
        from pathlib import Path

        import qcflow

        # Create some files to preserve as artifacts
        features = "rooms, zipcode, median_price, school_rating, transport"
        data = {"state": "TX", "Available": 25, "Type": "Detached"}
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_dir = Path(tmp_dir)
            with (tmp_dir / "data.json").open("w") as f:
                json.dump(data, f, indent=2)
            with (tmp_dir / "features.json").open("w") as f:
                f.write(features)
            # Write all files in `tmp_dir` to root artifact_uri/states
            with qcflow.start_run():
                qcflow.log_artifacts(tmp_dir, artifact_path="states")
    """
    run_id = run_id or _get_or_start_run().info.run_id
    QCFlowClient().log_artifacts(run_id, local_dir, artifact_path)


def log_text(text: str, artifact_file: str, run_id: Optional[str] = None) -> None:
    """
    Log text as an artifact.

    Args:
        text: String containing text to log.
        artifact_file: The run-relative artifact file path in posixpath format to which
            the text is saved (e.g. "dir/file.txt").
        run_id: If specified, log the artifact to the specified run. If not specified, log the
            artifact to the currently active run.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        with qcflow.start_run():
            # Log text to a file under the run's root artifact directory
            qcflow.log_text("text1", "file1.txt")

            # Log text in a subdirectory of the run's root artifact directory
            qcflow.log_text("text2", "dir/file2.txt")

            # Log HTML text
            qcflow.log_text("<h1>header</h1>", "index.html")

    """
    run_id = run_id or _get_or_start_run().info.run_id
    QCFlowClient().log_text(run_id, text, artifact_file)


def log_dict(dictionary: dict[str, Any], artifact_file: str, run_id: Optional[str] = None) -> None:
    """
    Log a JSON/YAML-serializable object (e.g. `dict`) as an artifact. The serialization
    format (JSON or YAML) is automatically inferred from the extension of `artifact_file`.
    If the file extension doesn't exist or match any of [".json", ".yml", ".yaml"],
    JSON format is used.

    Args:
        dictionary: Dictionary to log.
        artifact_file: The run-relative artifact file path in posixpath format to which
            the dictionary is saved (e.g. "dir/data.json").
        run_id: If specified, log the dictionary to the specified run. If not specified, log the
            dictionary to the currently active run.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        dictionary = {"k": "v"}

        with qcflow.start_run():
            # Log a dictionary as a JSON file under the run's root artifact directory
            qcflow.log_dict(dictionary, "data.json")

            # Log a dictionary as a YAML file in a subdirectory of the run's root artifact directory
            qcflow.log_dict(dictionary, "dir/data.yml")

            # If the file extension doesn't exist or match any of [".json", ".yaml", ".yml"],
            # JSON format is used.
            qcflow.log_dict(dictionary, "data")
            qcflow.log_dict(dictionary, "data.txt")

    """
    run_id = run_id or _get_or_start_run().info.run_id
    QCFlowClient().log_dict(run_id, dictionary, artifact_file)


def log_figure(
    figure: Union["matplotlib.figure.Figure", "plotly.graph_objects.Figure"],
    artifact_file: str,
    *,
    save_kwargs: Optional[dict[str, Any]] = None,
) -> None:
    """
    Log a figure as an artifact. The following figure objects are supported:

    - `matplotlib.figure.Figure`_
    - `plotly.graph_objects.Figure`_

    .. _matplotlib.figure.Figure:
        https://matplotlib.org/api/_as_gen/matplotlib.figure.Figure.html

    .. _plotly.graph_objects.Figure:
        https://plotly.com/python-api-reference/generated/plotly.graph_objects.Figure.html

    Args:
        figure: Figure to log.
        artifact_file: The run-relative artifact file path in posixpath format to which
            the figure is saved (e.g. "dir/file.png").
        save_kwargs: Additional keyword arguments passed to the method that saves the figure.

    .. code-block:: python
        :test:
        :caption: Matplotlib Example

        import qcflow
        import matplotlib.pyplot as plt

        fig, ax = plt.subplots()
        ax.plot([0, 1], [2, 3])

        with qcflow.start_run():
            qcflow.log_figure(fig, "figure.png")

    .. code-block:: python
        :test:
        :caption: Plotly Example

        import qcflow
        from plotly import graph_objects as go

        fig = go.Figure(go.Scatter(x=[0, 1], y=[2, 3]))

        with qcflow.start_run():
            qcflow.log_figure(fig, "figure.html")
    """
    run_id = _get_or_start_run().info.run_id
    QCFlowClient().log_figure(run_id, figure, artifact_file, save_kwargs=save_kwargs)


def log_image(
    image: Union["numpy.ndarray", "PIL.Image.Image", "qcflow.Image"],
    artifact_file: Optional[str] = None,
    key: Optional[str] = None,
    step: Optional[int] = None,
    timestamp: Optional[int] = None,
    synchronous: Optional[bool] = False,
) -> None:
    """
    Logs an image in QCFlow, supporting two use cases:

    1. Time-stepped image logging:
        Ideal for tracking changes or progressions through iterative processes (e.g.,
        during model training phases).

        - Usage: :code:`log_image(image, key=key, step=step, timestamp=timestamp)`

    2. Artifact file image logging:
        Best suited for static image logging where the image is saved directly as a file
        artifact.

        - Usage: :code:`log_image(image, artifact_file)`

    The following image formats are supported:
        - `numpy.ndarray`_
        - `PIL.Image.Image`_

        .. _numpy.ndarray:
            https://numpy.org/doc/stable/reference/generated/numpy.ndarray.html

        .. _PIL.Image.Image:
            https://pillow.readthedocs.io/en/stable/reference/Image.html#PIL.Image.Image

        - :class:`qcflow.Image`: An QCFlow wrapper around PIL image for convenient image logging.

    Numpy array support
        - data types:

            - bool (useful for logging image masks)
            - integer [0, 255]
            - unsigned integer [0, 255]
            - float [0.0, 1.0]

            .. warning::

                - Out-of-range integer values will raise ValueError.
                - Out-of-range float values will auto-scale with min/max and warn.

        - shape (H: height, W: width):

            - H x W (Grayscale)
            - H x W x 1 (Grayscale)
            - H x W x 3 (an RGB channel order is assumed)
            - H x W x 4 (an RGBA channel order is assumed)

    Args:
        image: The image object to be logged.
        artifact_file: Specifies the path, in POSIX format, where the image
            will be stored as an artifact relative to the run's root directory (for
            example, "dir/image.png"). This parameter is kept for backward compatibility
            and should not be used together with `key`, `step`, or `timestamp`.
        key: Image name for time-stepped image logging. This string may only contain
            alphanumerics, underscores (_), dashes (-), periods (.), spaces ( ), and
            slashes (/).
        step: Integer training step (iteration) at which the image was saved.
            Defaults to 0.
        timestamp: Time when this image was saved. Defaults to the current system time.
        synchronous: *Experimental* If True, blocks until the image is logged successfully.

    .. code-block:: python
        :caption: Time-stepped image logging numpy example

        import qcflow
        import numpy as np

        image = np.random.randint(0, 256, size=(100, 100, 3), dtype=np.uint8)

        with qcflow.start_run():
            qcflow.log_image(image, key="dogs", step=3)

    .. code-block:: python
        :caption: Time-stepped image logging pillow example

        import qcflow
        from PIL import Image

        image = Image.new("RGB", (100, 100))

        with qcflow.start_run():
            qcflow.log_image(image, key="dogs", step=3)

    .. code-block:: python
        :caption: Time-stepped image logging with qcflow.Image example

        import qcflow
        from PIL import Image

        # If you have a preexisting saved image
        Image.new("RGB", (100, 100)).save("image.png")

        image = qcflow.Image("image.png")
        with qcflow.start_run() as run:
            qcflow.log_image(run.info.run_id, image, key="dogs", step=3)

    .. code-block:: python
        :caption: Legacy artifact file image logging numpy example

        import qcflow
        import numpy as np

        image = np.random.randint(0, 256, size=(100, 100, 3), dtype=np.uint8)

        with qcflow.start_run():
            qcflow.log_image(image, "image.png")

    .. code-block:: python
        :caption: Legacy artifact file image logging pillow example

        import qcflow
        from PIL import Image

        image = Image.new("RGB", (100, 100))

        with qcflow.start_run():
            qcflow.log_image(image, "image.png")
    """
    run_id = _get_or_start_run().info.run_id
    QCFlowClient().log_image(run_id, image, artifact_file, key, step, timestamp, synchronous)


@experimental
def log_table(
    data: Union[dict[str, Any], "pandas.DataFrame"],
    artifact_file: str,
    run_id: Optional[str] = None,
) -> None:
    """
    Log a table to QCFlow Tracking as a JSON artifact. If the artifact_file already exists
    in the run, the data would be appended to the existing artifact_file.

    Args:
        data: Dictionary or pandas.DataFrame to log.
        artifact_file: The run-relative artifact file path in posixpath format to which
            the table is saved (e.g. "dir/file.json").
        run_id: If specified, log the table to the specified run. If not specified, log the
            table to the currently active run.

    .. code-block:: python
        :test:
        :caption: Dictionary Example

        import qcflow

        table_dict = {
            "inputs": ["What is QCFlow?", "What is Databricks?"],
            "outputs": ["QCFlow is ...", "Databricks is ..."],
            "toxicity": [0.0, 0.0],
        }
        with qcflow.start_run():
            # Log the dictionary as a table
            qcflow.log_table(data=table_dict, artifact_file="qabot_eval_results.json")

    .. code-block:: python
        :test:
        :caption: Pandas DF Example

        import qcflow
        import pandas as pd

        table_dict = {
            "inputs": ["What is QCFlow?", "What is Databricks?"],
            "outputs": ["QCFlow is ...", "Databricks is ..."],
            "toxicity": [0.0, 0.0],
        }
        df = pd.DataFrame.from_dict(table_dict)
        with qcflow.start_run():
            # Log the df as a table
            qcflow.log_table(data=df, artifact_file="qabot_eval_results.json")
    """
    run_id = run_id or _get_or_start_run().info.run_id
    QCFlowClient().log_table(run_id, data, artifact_file)


@experimental
def load_table(
    artifact_file: str,
    run_ids: Optional[list[str]] = None,
    extra_columns: Optional[list[str]] = None,
) -> "pandas.DataFrame":
    """
    Load a table from QCFlow Tracking as a pandas.DataFrame. The table is loaded from the
    specified artifact_file in the specified run_ids. The extra_columns are columns that
    are not in the table but are augmented with run information and added to the DataFrame.

    Args:
        artifact_file: The run-relative artifact file path in posixpath format to which
            table to load (e.g. "dir/file.json").
        run_ids: Optional list of run_ids to load the table from. If no run_ids are specified,
            the table is loaded from all runs in the current experiment.
        extra_columns: Optional list of extra columns to add to the returned DataFrame
            For example, if extra_columns=["run_id"], then the returned DataFrame
            will have a column named run_id.

    Returns:
        pandas.DataFrame containing the loaded table if the artifact exists
        or else throw a QCFlowException.

    .. code-block:: python
        :test:
        :caption: Example with passing run_ids

        import qcflow

        table_dict = {
            "inputs": ["What is QCFlow?", "What is Databricks?"],
            "outputs": ["QCFlow is ...", "Databricks is ..."],
            "toxicity": [0.0, 0.0],
        }

        with qcflow.start_run() as run:
            # Log the dictionary as a table
            qcflow.log_table(data=table_dict, artifact_file="qabot_eval_results.json")
            run_id = run.info.run_id

        loaded_table = qcflow.load_table(
            artifact_file="qabot_eval_results.json",
            run_ids=[run_id],
            # Append a column containing the associated run ID for each row
            extra_columns=["run_id"],
        )

    .. code-block:: python
        :test:
        :caption: Example with passing no run_ids

        # Loads the table with the specified name for all runs in the given
        # experiment and joins them together
        import qcflow

        table_dict = {
            "inputs": ["What is QCFlow?", "What is Databricks?"],
            "outputs": ["QCFlow is ...", "Databricks is ..."],
            "toxicity": [0.0, 0.0],
        }

        with qcflow.start_run():
            # Log the dictionary as a table
            qcflow.log_table(data=table_dict, artifact_file="qabot_eval_results.json")

        loaded_table = qcflow.load_table(
            "qabot_eval_results.json",
            # Append the run ID and the parent run ID to the table
            extra_columns=["run_id"],
        )
    """
    experiment_id = _get_experiment_id()
    return QCFlowClient().load_table(experiment_id, artifact_file, run_ids, extra_columns)


def _record_logged_model(qcflow_model, run_id=None):
    run_id = run_id or _get_or_start_run().info.run_id
    QCFlowClient()._record_logged_model(run_id, qcflow_model)


def get_experiment(experiment_id: str) -> Experiment:
    """Retrieve an experiment by experiment_id from the backend store

    Args:
        experiment_id: The string-ified experiment ID returned from ``create_experiment``.

    Returns:
        :py:class:`qcflow.entities.Experiment`

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        experiment = qcflow.get_experiment("0")
        print(f"Name: {experiment.name}")
        print(f"Artifact Location: {experiment.artifact_location}")
        print(f"Tags: {experiment.tags}")
        print(f"Lifecycle_stage: {experiment.lifecycle_stage}")
        print(f"Creation timestamp: {experiment.creation_time}")

    .. code-block:: text
        :caption: Output

        Name: Default
        Artifact Location: file:///.../mlruns/0
        Tags: {}
        Lifecycle_stage: active
        Creation timestamp: 1662004217511
    """
    return QCFlowClient().get_experiment(experiment_id)


def get_experiment_by_name(name: str) -> Optional[Experiment]:
    """
    Retrieve an experiment by experiment name from the backend store

    Args:
        name: The case sensitive experiment name.

    Returns:
        An instance of :py:class:`qcflow.entities.Experiment`
        if an experiment with the specified name exists, otherwise None.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        # Case sensitive name
        experiment = qcflow.get_experiment_by_name("Default")
        print(f"Experiment_id: {experiment.experiment_id}")
        print(f"Artifact Location: {experiment.artifact_location}")
        print(f"Tags: {experiment.tags}")
        print(f"Lifecycle_stage: {experiment.lifecycle_stage}")
        print(f"Creation timestamp: {experiment.creation_time}")

    .. code-block:: text
        :caption: Output

        Experiment_id: 0
        Artifact Location: file:///.../mlruns/0
        Tags: {}
        Lifecycle_stage: active
        Creation timestamp: 1662004217511
    """
    return QCFlowClient().get_experiment_by_name(name)


def search_experiments(
    view_type: int = ViewType.ACTIVE_ONLY,
    max_results: Optional[int] = None,
    filter_string: Optional[str] = None,
    order_by: Optional[list[str]] = None,
) -> list[Experiment]:
    """
    Search for experiments that match the specified search query.

    Args:
        view_type: One of enum values ``ACTIVE_ONLY``, ``DELETED_ONLY``, or ``ALL``
            defined in :py:class:`qcflow.entities.ViewType`.
        max_results: If passed, specifies the maximum number of experiments desired. If not
            passed, all experiments will be returned.
        filter_string: Filter query string (e.g., ``"name = 'my_experiment'"``), defaults to
            searching for all experiments. The following identifiers, comparators, and logical
            operators are supported.

            Identifiers
              - ``name``: Experiment name
              - ``creation_time``: Experiment creation time
              - ``last_update_time``: Experiment last update time
              - ``tags.<tag_key>``: Experiment tag. If ``tag_key`` contains
                spaces, it must be wrapped with backticks (e.g., ``"tags.`extra key`"``).

            Comparators for string attributes and tags
                - ``=``: Equal to
                - ``!=``: Not equal to
                - ``LIKE``: Case-sensitive pattern match
                - ``ILIKE``: Case-insensitive pattern match

            Comparators for numeric attributes
                - ``=``: Equal to
                - ``!=``: Not equal to
                - ``<``: Less than
                - ``<=``: Less than or equal to
                - ``>``: Greater than
                - ``>=``: Greater than or equal to

            Logical operators
              - ``AND``: Combines two sub-queries and returns True if both of them are True.

        order_by: List of columns to order by. The ``order_by`` column can contain an optional
            ``DESC`` or ``ASC`` value (e.g., ``"name DESC"``). The default ordering is ``ASC``,
            so ``"name"`` is equivalent to ``"name ASC"``. If unspecified, defaults to
            ``["last_update_time DESC"]``, which lists experiments updated most recently first.
            The following fields are supported:

                - ``experiment_id``: Experiment ID
                - ``name``: Experiment name
                - ``creation_time``: Experiment creation time
                - ``last_update_time``: Experiment last update time

    Returns:
        A list of :py:class:`Experiment <qcflow.entities.Experiment>` objects.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow


        def assert_experiment_names_equal(experiments, expected_names):
            actual_names = [e.name for e in experiments if e.name != "Default"]
            assert actual_names == expected_names, (actual_names, expected_names)


        qcflow.set_tracking_uri("sqlite:///:memory:")
        # Create experiments
        for name, tags in [
            ("a", None),
            ("b", None),
            ("ab", {"k": "v"}),
            ("bb", {"k": "V"}),
        ]:
            qcflow.create_experiment(name, tags=tags)

        # Search for experiments with name "a"
        experiments = qcflow.search_experiments(filter_string="name = 'a'")
        assert_experiment_names_equal(experiments, ["a"])
        # Search for experiments with name starting with "a"
        experiments = qcflow.search_experiments(filter_string="name LIKE 'a%'")
        assert_experiment_names_equal(experiments, ["ab", "a"])
        # Search for experiments with tag key "k" and value ending with "v" or "V"
        experiments = qcflow.search_experiments(filter_string="tags.k ILIKE '%v'")
        assert_experiment_names_equal(experiments, ["bb", "ab"])
        # Search for experiments with name ending with "b" and tag {"k": "v"}
        experiments = qcflow.search_experiments(filter_string="name LIKE '%b' AND tags.k = 'v'")
        assert_experiment_names_equal(experiments, ["ab"])
        # Sort experiments by name in ascending order
        experiments = qcflow.search_experiments(order_by=["name"])
        assert_experiment_names_equal(experiments, ["a", "ab", "b", "bb"])
        # Sort experiments by ID in descending order
        experiments = qcflow.search_experiments(order_by=["experiment_id DESC"])
        assert_experiment_names_equal(experiments, ["bb", "ab", "b", "a"])
    """

    def pagination_wrapper_func(number_to_get, next_page_token):
        return QCFlowClient().search_experiments(
            view_type=view_type,
            max_results=number_to_get,
            filter_string=filter_string,
            order_by=order_by,
            page_token=next_page_token,
        )

    return get_results_from_paginated_fn(
        pagination_wrapper_func,
        SEARCH_MAX_RESULTS_DEFAULT,
        max_results,
    )


def create_experiment(
    name: str,
    artifact_location: Optional[str] = None,
    tags: Optional[dict[str, Any]] = None,
) -> str:
    """
    Create an experiment.

    Args:
        name: The experiment name, which must be a unique string.
        artifact_location: The location to store run artifacts. If not provided, the server picks
            an appropriate default.
        tags: An optional dictionary of string keys and values to set as tags on the experiment.

    Returns:
        String ID of the created experiment.

     .. code-block:: python
        :test:
        :caption: Example

        import qcflow
        from pathlib import Path

        # Create an experiment name, which must be unique and case sensitive
        experiment_id = qcflow.create_experiment(
            "Social NLP Experiments",
            artifact_location=Path.cwd().joinpath("mlruns").as_uri(),
            tags={"version": "v1", "priority": "P1"},
        )
        experiment = qcflow.get_experiment(experiment_id)
        print(f"Name: {experiment.name}")
        print(f"Experiment_id: {experiment.experiment_id}")
        print(f"Artifact Location: {experiment.artifact_location}")
        print(f"Tags: {experiment.tags}")
        print(f"Lifecycle_stage: {experiment.lifecycle_stage}")
        print(f"Creation timestamp: {experiment.creation_time}")

    .. code-block:: text
        :caption: Output

        Name: Social NLP Experiments
        Experiment_id: 1
        Artifact Location: file:///.../mlruns
        Tags: {'version': 'v1', 'priority': 'P1'}
        Lifecycle_stage: active
        Creation timestamp: 1662004217511
    """
    return QCFlowClient().create_experiment(name, artifact_location, tags)


def delete_experiment(experiment_id: str) -> None:
    """
    Delete an experiment from the backend store.

    Args:
        experiment_id: The string-ified experiment ID returned from ``create_experiment``.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        experiment_id = qcflow.create_experiment("New Experiment")
        qcflow.delete_experiment(experiment_id)

        # Examine the deleted experiment details.
        experiment = qcflow.get_experiment(experiment_id)
        print(f"Name: {experiment.name}")
        print(f"Artifact Location: {experiment.artifact_location}")
        print(f"Lifecycle_stage: {experiment.lifecycle_stage}")
        print(f"Last Updated timestamp: {experiment.last_update_time}")

    .. code-block:: text
        :caption: Output

        Name: New Experiment
        Artifact Location: file:///.../mlruns/2
        Lifecycle_stage: deleted
        Last Updated timestamp: 1662004217511

    """
    QCFlowClient().delete_experiment(experiment_id)


def delete_run(run_id: str) -> None:
    """
    Deletes a run with the given ID.

    Args:
        run_id: Unique identifier for the run to delete.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        with qcflow.start_run() as run:
            qcflow.log_param("p", 0)

        run_id = run.info.run_id
        qcflow.delete_run(run_id)

        lifecycle_stage = qcflow.get_run(run_id).info.lifecycle_stage
        print(f"run_id: {run_id}; lifecycle_stage: {lifecycle_stage}")

    .. code-block:: text
        :caption: Output

        run_id: 45f4af3e6fd349e58579b27fcb0b8277; lifecycle_stage: deleted

    """
    QCFlowClient().delete_run(run_id)


def get_artifact_uri(artifact_path: Optional[str] = None) -> str:
    """
    Get the absolute URI of the specified artifact in the currently active run.

    If `path` is not specified, the artifact root URI of the currently active
    run will be returned; calls to ``log_artifact`` and ``log_artifacts`` write
    artifact(s) to subdirectories of the artifact root URI.

    If no run is active, this method will create a new active run.

    Args:
        artifact_path: The run-relative artifact path for which to obtain an absolute URI.
            For example, "path/to/artifact". If unspecified, the artifact root URI
            for the currently active run will be returned.

    Returns:
        An *absolute* URI referring to the specified artifact or the currently active run's
        artifact root. For example, if an artifact path is provided and the currently active
        run uses an S3-backed store, this may be a uri of the form
        ``s3://<bucket_name>/path/to/artifact/root/path/to/artifact``. If an artifact path
        is not provided and the currently active run uses an S3-backed store, this may be a
        URI of the form ``s3://<bucket_name>/path/to/artifact/root``.

    .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        features = "rooms, zipcode, median_price, school_rating, transport"
        with open("features.txt", "w") as f:
            f.write(features)

        # Log the artifact in a directory "features" under the root artifact_uri/features
        with qcflow.start_run():
            qcflow.log_artifact("features.txt", artifact_path="features")

            # Fetch the artifact uri root directory
            artifact_uri = qcflow.get_artifact_uri()
            print(f"Artifact uri: {artifact_uri}")

            # Fetch a specific artifact uri
            artifact_uri = qcflow.get_artifact_uri(artifact_path="features/features.txt")
            print(f"Artifact uri: {artifact_uri}")

    .. code-block:: text
        :caption: Output

        Artifact uri: file:///.../0/a46a80f1c9644bd8f4e5dd5553fffce/artifacts
        Artifact uri: file:///.../0/a46a80f1c9644bd8f4e5dd5553fffce/artifacts/features/features.txt
    """
    return artifact_utils.get_artifact_uri(
        run_id=_get_or_start_run().info.run_id, artifact_path=artifact_path
    )


def search_runs(
    experiment_ids: Optional[list[str]] = None,
    filter_string: str = "",
    run_view_type: int = ViewType.ACTIVE_ONLY,
    max_results: int = SEARCH_MAX_RESULTS_PANDAS,
    order_by: Optional[list[str]] = None,
    output_format: str = "pandas",
    search_all_experiments: bool = False,
    experiment_names: Optional[list[str]] = None,
) -> Union[list[Run], "pandas.DataFrame"]:
    """
    Search for Runs that fit the specified criteria.

    Args:
        experiment_ids: List of experiment IDs. Search can work with experiment IDs or
            experiment names, but not both in the same call. Values other than
            ``None`` or ``[]`` will result in error if ``experiment_names`` is
            also not ``None`` or ``[]``. ``None`` will default to the active
            experiment if ``experiment_names`` is ``None`` or ``[]``.
        filter_string: Filter query string, defaults to searching all runs.
        run_view_type: one of enum values ``ACTIVE_ONLY``, ``DELETED_ONLY``, or ``ALL`` runs
            defined in :py:class:`qcflow.entities.ViewType`.
        max_results: The maximum number of runs to put in the dataframe. Default is 100,000
            to avoid causing out-of-memory issues on the user's machine.
        order_by: List of columns to order by (e.g., "metrics.rmse"). The ``order_by`` column
            can contain an optional ``DESC`` or ``ASC`` value. The default is ``ASC``.
            The default ordering is to sort by ``start_time DESC``, then ``run_id``.
        output_format: The output format to be returned. If ``pandas``, a ``pandas.DataFrame``
            is returned and, if ``list``, a list of :py:class:`qcflow.entities.Run`
            is returned.
        search_all_experiments: Boolean specifying whether all experiments should be searched.
            Only honored if ``experiment_ids`` is ``[]`` or ``None``.
        experiment_names: List of experiment names. Search can work with experiment IDs or
            experiment names, but not both in the same call. Values other
            than ``None`` or ``[]`` will result in error if ``experiment_ids``
            is also not ``None`` or ``[]``. ``None`` will default to the active
            experiment if ``experiment_ids`` is ``None`` or ``[]``.

    Returns:
        If output_format is ``list``: a list of :py:class:`qcflow.entities.Run`. If
        output_format is ``pandas``: ``pandas.DataFrame`` of runs, where each metric,
        parameter, and tag is expanded into its own column named metrics.*, params.*, or
        tags.* respectively. For runs that don't have a particular metric, parameter, or tag,
        the value for the corresponding column is (NumPy) ``Nan``, ``None``, or ``None``
        respectively.

     .. code-block:: python
        :test:
        :caption: Example

        import qcflow

        # Create an experiment and log two runs under it
        experiment_name = "Social NLP Experiments"
        experiment_id = qcflow.create_experiment(experiment_name)
        with qcflow.start_run(experiment_id=experiment_id):
            qcflow.log_metric("m", 1.55)
            qcflow.set_tag("s.release", "1.1.0-RC")
        with qcflow.start_run(experiment_id=experiment_id):
            qcflow.log_metric("m", 2.50)
            qcflow.set_tag("s.release", "1.2.0-GA")
        # Search for all the runs in the experiment with the given experiment ID
        df = qcflow.search_runs([experiment_id], order_by=["metrics.m DESC"])
        print(df[["metrics.m", "tags.s.release", "run_id"]])
        print("--")
        # Search the experiment_id using a filter_string with tag
        # that has a case insensitive pattern
        filter_string = "tags.s.release ILIKE '%rc%'"
        df = qcflow.search_runs([experiment_id], filter_string=filter_string)
        print(df[["metrics.m", "tags.s.release", "run_id"]])
        print("--")
        # Search for all the runs in the experiment with the given experiment name
        df = qcflow.search_runs(experiment_names=[experiment_name], order_by=["metrics.m DESC"])
        print(df[["metrics.m", "tags.s.release", "run_id"]])

    .. code-block:: text
        :caption: Output

           metrics.m tags.s.release                            run_id
        0       2.50       1.2.0-GA  147eed886ab44633902cc8e19b2267e2
        1       1.55       1.1.0-RC  5cc7feaf532f496f885ad7750809c4d4
        --
           metrics.m tags.s.release                            run_id
        0       1.55       1.1.0-RC  5cc7feaf532f496f885ad7750809c4d4
        --
           metrics.m tags.s.release                            run_id
        0       2.50       1.2.0-GA  147eed886ab44633902cc8e19b2267e2
        1       1.55       1.1.0-RC  5cc7feaf532f496f885ad7750809c4d4
    """
    no_ids = experiment_ids is None or len(experiment_ids) == 0
    no_names = experiment_names is None or len(experiment_names) == 0
    no_ids_or_names = no_ids and no_names
    if not no_ids and not no_names:
        raise QCFlowException(
            message="Only experiment_ids or experiment_names can be used, but not both",
            error_code=INVALID_PARAMETER_VALUE,
        )

    if search_all_experiments and no_ids_or_names:
        experiment_ids = [
            exp.experiment_id for exp in search_experiments(view_type=ViewType.ACTIVE_ONLY)
        ]
    elif no_ids_or_names:
        experiment_ids = [_get_experiment_id()]
    elif not no_names:
        experiments = []
        for n in experiment_names:
            if n is not None:
                experiment_by_name = get_experiment_by_name(n)
                if experiment_by_name:
                    experiments.append(experiment_by_name)
                else:
                    _logger.warning("Cannot retrieve experiment by name %s", n)
        experiment_ids = [e.experiment_id for e in experiments if e is not None]

    if len(experiment_ids) == 0:
        runs = []
    else:
        # Using an internal function as the linter doesn't like assigning a lambda, and inlining the
        # full thing is a mess
        def pagination_wrapper_func(number_to_get, next_page_token):
            return QCFlowClient().search_runs(
                experiment_ids,
                filter_string,
                run_view_type,
                number_to_get,
                order_by,
                next_page_token,
            )

        runs = get_results_from_paginated_fn(
            pagination_wrapper_func,
            NUM_RUNS_PER_PAGE_PANDAS,
            max_results,
        )

    if output_format == "list":
        return runs  # List[qcflow.entities.run.Run]
    elif output_format == "pandas":
        import numpy as np
        import pandas as pd

        info = {
            "run_id": [],
            "experiment_id": [],
            "status": [],
            "artifact_uri": [],
            "start_time": [],
            "end_time": [],
        }
        params, metrics, tags = ({}, {}, {})
        PARAM_NULL, METRIC_NULL, TAG_NULL = (None, np.nan, None)
        for i, run in enumerate(runs):
            info["run_id"].append(run.info.run_id)
            info["experiment_id"].append(run.info.experiment_id)
            info["status"].append(run.info.status)
            info["artifact_uri"].append(run.info.artifact_uri)
            info["start_time"].append(pd.to_datetime(run.info.start_time, unit="ms", utc=True))
            info["end_time"].append(pd.to_datetime(run.info.end_time, unit="ms", utc=True))

            # Params
            param_keys = set(params.keys())
            for key in param_keys:
                if key in run.data.params:
                    params[key].append(run.data.params[key])
                else:
                    params[key].append(PARAM_NULL)
            new_params = set(run.data.params.keys()) - param_keys
            for p in new_params:
                params[p] = [PARAM_NULL] * i  # Fill in null values for all previous runs
                params[p].append(run.data.params[p])

            # Metrics
            metric_keys = set(metrics.keys())
            for key in metric_keys:
                if key in run.data.metrics:
                    metrics[key].append(run.data.metrics[key])
                else:
                    metrics[key].append(METRIC_NULL)
            new_metrics = set(run.data.metrics.keys()) - metric_keys
            for m in new_metrics:
                metrics[m] = [METRIC_NULL] * i
                metrics[m].append(run.data.metrics[m])

            # Tags
            tag_keys = set(tags.keys())
            for key in tag_keys:
                if key in run.data.tags:
                    tags[key].append(run.data.tags[key])
                else:
                    tags[key].append(TAG_NULL)
            new_tags = set(run.data.tags.keys()) - tag_keys
            for t in new_tags:
                tags[t] = [TAG_NULL] * i
                tags[t].append(run.data.tags[t])

        data = {}
        data.update(info)
        for key, value in metrics.items():
            data["metrics." + key] = value
        for key, value in params.items():
            data["params." + key] = value
        for key, value in tags.items():
            data["tags." + key] = value
        return pd.DataFrame(data)
    else:
        raise ValueError(
            f"Unsupported output format: {output_format}. Supported string values are 'pandas' "
            "or 'list'"
        )


def _get_or_start_run():
    active_run_stack = _active_run_stack.get()
    if len(active_run_stack) > 0:
        return active_run_stack[-1]
    return start_run()


def _get_experiment_id_from_env():
    experiment_name = QCFLOW_EXPERIMENT_NAME.get()
    experiment_id = QCFLOW_EXPERIMENT_ID.get()
    if experiment_name is not None:
        exp = QCFlowClient().get_experiment_by_name(experiment_name)
        if exp:
            if experiment_id and experiment_id != exp.experiment_id:
                raise QCFlowException(
                    message=f"The provided {QCFLOW_EXPERIMENT_ID} environment variable "
                    f"value `{experiment_id}` does not match the experiment id "
                    f"`{exp.experiment_id}` for experiment name `{experiment_name}`",
                    error_code=INVALID_PARAMETER_VALUE,
                )
            else:
                return exp.experiment_id
        else:
            return QCFlowClient().create_experiment(name=experiment_name)
    if experiment_id is not None:
        try:
            exp = QCFlowClient().get_experiment(experiment_id)
            return exp.experiment_id
        except QCFlowException as exc:
            raise QCFlowException(
                message=f"The provided {QCFLOW_EXPERIMENT_ID} environment variable "
                f"value `{experiment_id}` does not exist in the tracking server. Provide a valid "
                f"experiment_id.",
                error_code=INVALID_PARAMETER_VALUE,
            ) from exc


def _get_experiment_id():
    if _active_experiment_id:
        return _active_experiment_id
    else:
        return _get_experiment_id_from_env() or default_experiment_registry.get_experiment_id()


@autologging_integration("qcflow")
def autolog(
    log_input_examples: bool = False,
    log_model_signatures: bool = True,
    log_models: bool = True,
    log_datasets: bool = True,
    log_traces: bool = True,
    disable: bool = False,
    exclusive: bool = False,
    disable_for_unsupported_versions: bool = False,
    silent: bool = False,
    extra_tags: Optional[dict[str, str]] = None,
    exclude_flavors: Optional[list[str]] = None,
) -> None:
    """
    Enables (or disables) and configures autologging for all supported integrations.

    The parameters are passed to any autologging integrations that support them.

    See the :ref:`tracking docs <automatic-logging>` for a list of supported autologging
    integrations.

    Note that framework-specific configurations set at any point will take precedence over
    any configurations set by this function. For example:

    .. code-block:: python
        :test:

        import qcflow

        qcflow.autolog(log_models=False, exclusive=True)
        import sklearn

    would enable autologging for `sklearn` with `log_models=False` and `exclusive=True`,
    but

    .. code-block:: python
        :test:

        import qcflow

        qcflow.autolog(log_models=False, exclusive=True)

        import sklearn

        qcflow.sklearn.autolog(log_models=True)

    would enable autologging for `sklearn` with `log_models=True` and `exclusive=False`,
    the latter resulting from the default value for `exclusive` in `qcflow.sklearn.autolog`;
    other framework autolog functions (e.g. `qcflow.tensorflow.autolog`) would use the
    configurations set by `qcflow.autolog` (in this instance, `log_models=False`, `exclusive=True`),
    until they are explicitly called by the user.

    Args:
        log_input_examples: If ``True``, input examples from training datasets are collected and
            logged along with model artifacts during training. If ``False``,
            input examples are not logged.
            Note: Input examples are QCFlow model attributes
            and are only collected if ``log_models`` is also ``True``.
        log_model_signatures: If ``True``,
            :py:class:`ModelSignatures <qcflow.models.ModelSignature>`
            describing model inputs and outputs are collected and logged along
            with model artifacts during training. If ``False``, signatures are
            not logged. Note: Model signatures are QCFlow model attributes
            and are only collected if ``log_models`` is also ``True``.
        log_models: If ``True``, trained models are logged as QCFlow model artifacts.
            If ``False``, trained models are not logged.
            Input examples and model signatures, which are attributes of QCFlow models,
            are also omitted when ``log_models`` is ``False``.
        log_datasets: If ``True``, dataset information is logged to QCFlow Tracking.
            If ``False``, dataset information is not logged.
        log_traces: If ``True``, traces are collected for integrations.
            If ``False``, no trace is collected.
        disable: If ``True``, disables all supported autologging integrations. If ``False``,
            enables all supported autologging integrations.
        exclusive: If ``True``, autologged content is not logged to user-created fluent runs.
            If ``False``, autologged content is logged to the active fluent run,
            which may be user-created.
        disable_for_unsupported_versions: If ``True``, disable autologging for versions of
            all integration libraries that have not been tested against this version
            of the QCFlow client or are incompatible.
        silent: If ``True``, suppress all event logs and warnings from QCFlow during autologging
            setup and training execution. If ``False``, show all events and warnings during
            autologging setup and training execution.
        extra_tags: A dictionary of extra tags to set on each managed run created by autologging.
        exclude_flavors: A list of flavor names that are excluded from the auto-logging.
            e.g. tensorflow, pyspark.ml

    .. code-block:: python
        :test:
        :caption: Example

        import numpy as np
        import qcflow.sklearn
        from qcflow import QCFlowClient
        from sklearn.linear_model import LinearRegression


        def print_auto_logged_info(r):
            tags = {k: v for k, v in r.data.tags.items() if not k.startswith("qcflow.")}
            artifacts = [f.path for f in QCFlowClient().list_artifacts(r.info.run_id, "model")]
            print(f"run_id: {r.info.run_id}")
            print(f"artifacts: {artifacts}")
            print(f"params: {r.data.params}")
            print(f"metrics: {r.data.metrics}")
            print(f"tags: {tags}")


        # prepare training data
        X = np.array([[1, 1], [1, 2], [2, 2], [2, 3]])
        y = np.dot(X, np.array([1, 2])) + 3

        # Auto log all the parameters, metrics, and artifacts
        qcflow.autolog()
        model = LinearRegression()
        with qcflow.start_run() as run:
            model.fit(X, y)

        # fetch the auto logged parameters and metrics for ended run
        print_auto_logged_info(qcflow.get_run(run_id=run.info.run_id))

    .. code-block:: text
        :caption: Output

        run_id: fd10a17d028c47399a55ab8741721ef7
        artifacts: ['model/MLmodel', 'model/conda.yaml', 'model/model.pkl']
        params: {'copy_X': 'True',
                 'normalize': 'False',
                 'fit_intercept': 'True',
                 'n_jobs': 'None'}
        metrics: {'training_score': 1.0,
                  'training_root_mean_squared_error': 4.440892098500626e-16,
                  'training_r2_score': 1.0,
                  'training_mean_absolute_error': 2.220446049250313e-16,
                  'training_mean_squared_error': 1.9721522630525295e-31}
        tags: {'estimator_class': 'sklearn.linear_model._base.LinearRegression',
               'estimator_name': 'LinearRegression'}
    """
    locals_copy = locals().items()

    # Mapping of library name to specific autolog function name. We use string like
    # "tensorflow.autolog" to avoid loading all flavor modules, so we only set autologging for
    # compatible modules.
    LIBRARY_TO_AUTOLOG_MODULE = {
        "tensorflow": "qcflow.tensorflow",
        "keras": "qcflow.keras",
        "xgboost": "qcflow.xgboost",
        "lightgbm": "qcflow.lightgbm",
        "statsmodels": "qcflow.statsmodels",
        "sklearn": "qcflow.sklearn",
        "fastai": "qcflow.fastai",
        "pyspark": "qcflow.spark",
        "pyspark.ml": "qcflow.pyspark.ml",
        # TODO: Broaden this beyond pytorch_lightning as we add autologging support for more
        # Pytorch frameworks under qcflow.pytorch.autolog
        "pytorch_lightning": "qcflow.pytorch",
        "lightning": "qcflow.pytorch",
        "setfit": "qcflow.transformers",
        "transformers": "qcflow.transformers",
        # do not enable langchain autologging by default
    }

    GENAI_LIBRARY_TO_AUTOLOG_MODULE = {
        "anthropic": "qcflow.anthropic",
        "autogen": "qcflow.autogen",
        "openai": "qcflow.openai",
        "google.generativeai": "qcflow.gemini",
        "litellm": "qcflow.litellm",
        "llama_index.core": "qcflow.llama_index",
        "langchain": "qcflow.langchain",
        "dspy": "qcflow.dspy",
        "crewai": "qcflow.crewai",
        "boto3": "qcflow.bedrock",
    }

    # Currently, GenAI libraries are not enabled by `qcflow.autolog` in Databricks,
    # particularly when disable=False. This is because the function is automatically invoked
    # by system and we don't want to take the risk of enabling GenAI libraries all at once.
    # TODO: Remove this logic once a feature flag is implemented in Databricks Runtime init logic.
    if is_in_databricks_runtime() and (not disable):
        target_library_and_module = LIBRARY_TO_AUTOLOG_MODULE
    else:
        target_library_and_module = LIBRARY_TO_AUTOLOG_MODULE | GENAI_LIBRARY_TO_AUTOLOG_MODULE

    if exclude_flavors:
        excluded_modules = [f"qcflow.{flavor}" for flavor in exclude_flavors]
        target_library_and_module = {
            k: v for k, v in target_library_and_module.items() if v not in excluded_modules
        }

    def get_autologging_params(autolog_fn):
        try:
            needed_params = list(inspect.signature(autolog_fn).parameters.keys())
            return {k: v for k, v in locals_copy if k in needed_params}
        except Exception:
            return {}

    # Note: we need to protect `setup_autologging` with `autologging_conf_lock`,
    # because `setup_autologging` might be registered as post importing hook
    # and be executed asynchronously, so that it is out of current active
    # `autologging_conf_lock` scope.
    @autologging_conf_lock
    def setup_autologging(module):
        try:
            autologging_params = None
            autolog_module = importlib.import_module(target_library_and_module[module.__name__])
            autolog_fn = autolog_module.autolog
            # Only call integration's autolog function with `qcflow.autolog` configs
            # if the integration's autolog function has not already been called by the user.
            # Logic is as follows:
            # - if a previous_config exists, that means either `qcflow.autolog` or
            #   `qcflow.integration.autolog` was called.
            # - if the config contains `AUTOLOGGING_CONF_KEY_IS_GLOBALLY_CONFIGURED`, the
            #   configuration was set by `qcflow.autolog`, and so we can safely call `autolog_fn`
            #   with `autologging_params`.
            # - if the config doesn't contain this key, the configuration was set by an
            #   `qcflow.integration.autolog` call, so we should not call `autolog_fn` with
            #   new configs.
            prev_config = AUTOLOGGING_INTEGRATIONS.get(autolog_fn.integration_name)
            if prev_config and not prev_config.get(
                AUTOLOGGING_CONF_KEY_IS_GLOBALLY_CONFIGURED, False
            ):
                return

            autologging_params = get_autologging_params(autolog_fn)
            autolog_fn(**autologging_params)
            AUTOLOGGING_INTEGRATIONS[autolog_fn.integration_name][
                AUTOLOGGING_CONF_KEY_IS_GLOBALLY_CONFIGURED
            ] = True
            if not autologging_is_disabled(
                autolog_fn.integration_name
            ) and not autologging_params.get("silent", False):
                _logger.info("Autologging successfully enabled for %s.", module.__name__)
        except Exception as e:
            if is_testing():
                # Raise unexpected exceptions in test mode in order to detect
                # errors within dependent autologging integrations
                raise
            elif autologging_params is None or not autologging_params.get("silent", False):
                _logger.warning(
                    "Exception raised while enabling autologging for %s: %s",
                    module.__name__,
                    str(e),
                )

    # for each autolog library (except pyspark), register a post-import hook.
    # this way, we do not send any errors to the user until we know they are using the library.
    # the post-import hook also retroactively activates for previously-imported libraries.
    for library in sorted(set(target_library_and_module) - {"pyspark", "pyspark.ml"}):
        register_post_import_hook(setup_autologging, library, overwrite=True)

    if is_in_databricks_runtime():
        # for pyspark, we activate autologging immediately, without waiting for a module import.
        # this is because on Databricks a SparkSession already exists and the user can directly
        #   interact with it, and this activity should be logged.
        import pyspark as pyspark_module
        import pyspark.ml as pyspark_ml_module

        setup_autologging(pyspark_module)
        setup_autologging(pyspark_ml_module)
    else:
        if "pyspark" in target_library_and_module:
            register_post_import_hook(setup_autologging, "pyspark", overwrite=True)
        if "pyspark.ml" in target_library_and_module:
            register_post_import_hook(setup_autologging, "pyspark.ml", overwrite=True)