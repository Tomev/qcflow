from setuptools import find_packages, setup

setup(
    name="qcflow-test-plugin",
    version="0.0.1",
    description="Test plugin for QCFlow",
    packages=find_packages(),
    # Require QCFlow as a dependency of the plugin, so that plugin users can simply install
    # the plugin & then immediately use it with QCFlow
    install_requires=["qcflow"],
    entry_points={
        # Define a Tracking Store plugin for tracking URIs with scheme 'file-plugin'
        "qcflow.tracking_store": "file-plugin=qcflow_test_plugin.file_store:PluginFileStore",
        # Define a ArtifactRepository plugin for artifact URIs with scheme 'file-plugin'
        "qcflow.artifact_repository": (
            "file-plugin=qcflow_test_plugin.local_artifact:PluginLocalArtifactRepository"
        ),
        # Define a RunContextProvider plugin. The entry point name for run context providers
        # is not used, and so is set to the string "unused" here
        "qcflow.run_context_provider": (
            "unused=qcflow_test_plugin.run_context_provider:PluginRunContextProvider"
        ),
        # Define a DefaultExperimentProvider plugin. The entry point name for
        # default experiment providers is not used, and so is set to the string "unused" here
        "qcflow.default_experiment_provider": (
            "unused=qcflow_test_plugin.default_experiment_provider:PluginDefaultExperimentProvider"
        ),
        # Define a RequestHeaderProvider plugin. The entry point name for request header providers
        # is not used, and so is set to the string "unused" here
        "qcflow.request_header_provider": (
            "unused=qcflow_test_plugin.request_header_provider:PluginRequestHeaderProvider"
        ),
        # Define a RequestAuthProvider plugin. The entry point name for request auth providers
        # is not used, and so is set to the string "unused" here
        "qcflow.request_auth_provider": (
            "unused=qcflow_test_plugin.request_auth_provider:PluginRequestAuthProvider"
        ),
        # Define a Model Registry Store plugin for tracking URIs with scheme 'file-plugin'
        "qcflow.model_registry_store": (
            "file-plugin=qcflow_test_plugin.sqlalchemy_store:PluginRegistrySqlAlchemyStore"
        ),
        # Define a QCFlow Project Backend plugin called 'dummy-backend'
        "qcflow.project_backend": (
            "dummy-backend=qcflow_test_plugin.dummy_backend:PluginDummyProjectBackend"
        ),
        # Define a QCFlow model deployment plugin for target 'faketarget'
        "qcflow.deployments": "faketarget=qcflow_test_plugin.fake_deployment_plugin",
        # Define a QCFlow model evaluator with name "dummy_evaluator"
        "qcflow.model_evaluator": (
            "dummy_evaluator=qcflow_test_plugin.dummy_evaluator:DummyEvaluator"
        ),
        # Define a custom QCFlow application with name custom_app
        "qcflow.app": "custom_app=qcflow_test_plugin.app:custom_app",
        # Define an QCFlow dataset source called "dummy_source"
        "qcflow.dataset_source": (
            "dummy_source=qcflow_test_plugin.dummy_dataset_source:DummyDatasetSource"
        ),
        # Define an QCFlow dataset constructor called "from_dummy"
        "qcflow.dataset_constructor": "from_dummy=qcflow_test_plugin.dummy_dataset:from_dummy",
    },
)
