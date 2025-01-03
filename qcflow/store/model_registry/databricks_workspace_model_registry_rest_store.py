from qcflow.exceptions import QCFlowException
from qcflow.store.model_registry.rest_store import RestStore


def _raise_unsupported_method(method, message=None):
    messages = [
        f"Method '{method}' is unsupported for models in the Workspace Model Registry. "
        f"Upgrade to Models in Unity Catalog to access the latest features. You can configure "
        f"the QCFlow Python client to access models in Unity Catalog by running "
        f"qcflow.set_registry_uri('databricks-uc') before accessing models.",
    ]
    if message is not None:
        messages.append(message)
    raise QCFlowException(" ".join(messages))


class DatabricksWorkspaceModelRegistryRestStore(RestStore):
    def set_registered_model_alias(self, name, alias, version):
        _raise_unsupported_method(method="set_registered_model_alias")

    def delete_registered_model_alias(self, name, alias):
        _raise_unsupported_method(method="delete_registered_model_alias")

    def get_model_version_by_alias(self, name, alias):
        _raise_unsupported_method(
            method="get_model_version_by_alias",
            message="If attempting to load a model version by alias via a URI of the form "
            "'models:/model_name@alias_name', configure the QCFlow client to target Unity Catalog "
            "and try again.",
        )

    def _await_model_version_creation(self, mv, await_creation_for):
        uc_hint = (
            " For faster model version creation, use Models in Unity Catalog "
            "(https://docs.databricks.com/en/machine-learning/manage-model-lifecycle/index.html)."
        )
        self._await_model_version_creation_impl(mv, await_creation_for, hint=uc_hint)
