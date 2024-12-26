from abc import ABCMeta, abstractmethod

from qcflow.utils.annotations import developer_stable


@developer_stable
class DefaultExperimentProvider:
    """
    Abstract base class for objects that provide the ID of an QCFlow Experiment based on the
    current client context. For example, when the QCFlow client is running in a Databricks Job,
    a provider is used to obtain the ID of the QCFlow Experiment associated with the Job.

    Usually the experiment_id is set explicitly by the user, but if the experiment is not set,
    QCFlow computes a default experiment id based on different contexts.
    When an experiment is created via the fluent ``qcflow.start_run`` method, QCFlow iterates
    through the registered ``DefaultExperimentProvider``s until it finds one whose
    ``in_context()`` method returns ``True``; QCFlow then calls the provider's
    ``get_experiment_id()`` method and uses the resulting experiment ID for Tracking operations.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def in_context(self):
        """Determine if the QCFlow client is running in a context where this provider can
        identify an associated QCFlow Experiment ID.

        Returns:
            True if the QCFlow client is running in a context where the provider
            can identify an associated QCFlow Experiment ID. False otherwise.

        """

    @abstractmethod
    def get_experiment_id(self):
        """Provide the QCFlow Experiment ID for the current QCFlow client context.

        Assumes that ``in_context()`` is ``True``.

        Returns:
            The ID of the QCFlow Experiment associated with the current context.

        """
