from abc import ABCMeta, abstractmethod

from qcflow.utils.annotations import developer_stable


@developer_stable
class RunContextProvider:
    """
    Abstract base class for context provider objects specifying custom tags at run-creation time
    (e.g. tags specifying the git repo with which the run is associated).

    When a run is created via the fluent ``qcflow.start_run`` method, QCFlow iterates through all
    registered RunContextProviders. For each context provider where ``in_context`` returns ``True``,
    QCFlow calls the ``tags`` method on the context provider to compute context tags for the run.
    All context tags are then merged together and set on the newly-created run.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def in_context(self):
        """Determine if QCFlow is running in this context.

        Returns:
            bool indicating if in this context.

        """

    @abstractmethod
    def tags(self):
        """Generate context-specific tags.

        Returns:
            dict of tags.
        """
