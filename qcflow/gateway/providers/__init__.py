from qcflow.gateway.config import Provider
from qcflow.gateway.providers.base import BaseProvider


def get_provider(provider: Provider) -> type[BaseProvider]:
    from qcflow.gateway.provider_registry import provider_registry

    return provider_registry.get(provider)
