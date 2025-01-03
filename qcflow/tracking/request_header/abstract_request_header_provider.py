from abc import ABCMeta, abstractmethod

from qcflow.utils.annotations import developer_stable


@developer_stable
class RequestHeaderProvider:
    """
    Abstract base class for specifying custom request headers to add to outgoing requests
    (e.g. request headers specifying the environment from which qcflow is running).

    When a request is sent, QCFlow will iterate through all registered RequestHeaderProviders.
    For each provider where ``in_context`` returns ``True``, QCFlow calls the ``request_headers``
    method on the provider to compute request headers.

    All resulting request headers will then be merged together and sent with the request.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def in_context(self):
        """Determine if QCFlow is running in this context.

        Returns:
            bool indicating if in this context.

        """

    @abstractmethod
    def request_headers(self):
        """Generate context-specific request headers.

        Returns:
            dict of request headers.
        """
