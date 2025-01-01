# GENERATED FILE. PLEASE DON'T MODIFY.
# Run python3 ./dev/proto_to_graphql/code_generator.py to regenerate.
import graphene
import qcflow
from qcflow.server.graphql.graphql_custom_scalars import LongString
from qcflow.server.graphql.graphql_errors import ApiError
from qcflow.utils.proto_json_utils import parse_dict


class QCFlowModelVersionStatus(graphene.Enum):
    PENDING_REGISTRATION = 1
    FAILED_REGISTRATION = 2
    READY = 3


class QCFlowRunStatus(graphene.Enum):
    RUNNING = 1
    SCHEDULED = 2
    FINISHED = 3
    FAILED = 4
    KILLED = 5


class QCFlowViewType(graphene.Enum):
    ACTIVE_ONLY = 1
    DELETED_ONLY = 2
    ALL = 3


class QCFlowModelVersionTag(graphene.ObjectType):
    key = graphene.String()
    value = graphene.String()


class QCFlowModelVersion(graphene.ObjectType):
    name = graphene.String()
    version = graphene.String()
    creation_timestamp = LongString()
    last_updated_timestamp = LongString()
    user_id = graphene.String()
    current_stage = graphene.String()
    description = graphene.String()
    source = graphene.String()
    run_id = graphene.String()
    status = graphene.Field(QCFlowModelVersionStatus)
    status_message = graphene.String()
    tags = graphene.List(graphene.NonNull(QCFlowModelVersionTag))
    run_link = graphene.String()
    aliases = graphene.List(graphene.String)


class QCFlowSearchModelVersionsResponse(graphene.ObjectType):
    model_versions = graphene.List(graphene.NonNull(QCFlowModelVersion))
    next_page_token = graphene.String()
    apiError = graphene.Field(ApiError)


class QCFlowDatasetSummary(graphene.ObjectType):
    experiment_id = graphene.String()
    name = graphene.String()
    digest = graphene.String()
    context = graphene.String()


class QCFlowSearchDatasetsResponse(graphene.ObjectType):
    dataset_summaries = graphene.List(graphene.NonNull(QCFlowDatasetSummary))
    apiError = graphene.Field(ApiError)


class QCFlowMetricWithRunId(graphene.ObjectType):
    key = graphene.String()
    value = graphene.Float()
    timestamp = LongString()
    step = LongString()
    run_id = graphene.String()


class QCFlowGetMetricHistoryBulkIntervalResponse(graphene.ObjectType):
    metrics = graphene.List(graphene.NonNull(QCFlowMetricWithRunId))
    apiError = graphene.Field(ApiError)


class QCFlowFileInfo(graphene.ObjectType):
    path = graphene.String()
    is_dir = graphene.Boolean()
    file_size = LongString()


class QCFlowListArtifactsResponse(graphene.ObjectType):
    root_uri = graphene.String()
    files = graphene.List(graphene.NonNull(QCFlowFileInfo))
    next_page_token = graphene.String()
    apiError = graphene.Field(ApiError)


class QCFlowDataset(graphene.ObjectType):
    name = graphene.String()
    digest = graphene.String()
    source_type = graphene.String()
    source = graphene.String()
    schema = graphene.String()
    profile = graphene.String()


class QCFlowInputTag(graphene.ObjectType):
    key = graphene.String()
    value = graphene.String()


class QCFlowDatasetInput(graphene.ObjectType):
    tags = graphene.List(graphene.NonNull(QCFlowInputTag))
    dataset = graphene.Field(QCFlowDataset)


class QCFlowRunInputs(graphene.ObjectType):
    dataset_inputs = graphene.List(graphene.NonNull(QCFlowDatasetInput))


class QCFlowRunTag(graphene.ObjectType):
    key = graphene.String()
    value = graphene.String()


class QCFlowParam(graphene.ObjectType):
    key = graphene.String()
    value = graphene.String()


class QCFlowMetric(graphene.ObjectType):
    key = graphene.String()
    value = graphene.Float()
    timestamp = LongString()
    step = LongString()


class QCFlowRunData(graphene.ObjectType):
    metrics = graphene.List(graphene.NonNull(QCFlowMetric))
    params = graphene.List(graphene.NonNull(QCFlowParam))
    tags = graphene.List(graphene.NonNull(QCFlowRunTag))


class QCFlowRunInfo(graphene.ObjectType):
    run_id = graphene.String()
    run_uuid = graphene.String()
    run_name = graphene.String()
    experiment_id = graphene.String()
    user_id = graphene.String()
    status = graphene.Field(QCFlowRunStatus)
    start_time = LongString()
    end_time = LongString()
    artifact_uri = graphene.String()
    lifecycle_stage = graphene.String()


class QCFlowRun(graphene.ObjectType):
    info = graphene.Field(QCFlowRunInfo)
    data = graphene.Field(QCFlowRunData)
    inputs = graphene.Field(QCFlowRunInputs)


class QCFlowSearchRunsResponse(graphene.ObjectType):
    runs = graphene.List(graphene.NonNull('qcflow.server.graphql.graphql_schema_extensions.QCFlowRunExtension'))
    next_page_token = graphene.String()
    apiError = graphene.Field(ApiError)


class QCFlowGetRunResponse(graphene.ObjectType):
    run = graphene.Field('qcflow.server.graphql.graphql_schema_extensions.QCFlowRunExtension')
    apiError = graphene.Field(ApiError)


class QCFlowExperimentTag(graphene.ObjectType):
    key = graphene.String()
    value = graphene.String()


class QCFlowExperiment(graphene.ObjectType):
    experiment_id = graphene.String()
    name = graphene.String()
    artifact_location = graphene.String()
    lifecycle_stage = graphene.String()
    last_update_time = LongString()
    creation_time = LongString()
    tags = graphene.List(graphene.NonNull(QCFlowExperimentTag))


class QCFlowGetExperimentResponse(graphene.ObjectType):
    experiment = graphene.Field(QCFlowExperiment)
    apiError = graphene.Field(ApiError)


class QCFlowSearchModelVersionsInput(graphene.InputObjectType):
    filter = graphene.String()
    max_results = LongString()
    order_by = graphene.List(graphene.String)
    page_token = graphene.String()


class QCFlowSearchDatasetsInput(graphene.InputObjectType):
    experiment_ids = graphene.List(graphene.String)


class QCFlowGetMetricHistoryBulkIntervalInput(graphene.InputObjectType):
    run_ids = graphene.List(graphene.String)
    metric_key = graphene.String()
    start_step = graphene.Int()
    end_step = graphene.Int()
    max_results = graphene.Int()


class QCFlowListArtifactsInput(graphene.InputObjectType):
    run_id = graphene.String()
    run_uuid = graphene.String()
    path = graphene.String()
    page_token = graphene.String()


class QCFlowSearchRunsInput(graphene.InputObjectType):
    experiment_ids = graphene.List(graphene.String)
    filter = graphene.String()
    run_view_type = graphene.Field(QCFlowViewType)
    max_results = graphene.Int()
    order_by = graphene.List(graphene.String)
    page_token = graphene.String()


class QCFlowGetRunInput(graphene.InputObjectType):
    run_id = graphene.String()
    run_uuid = graphene.String()


class QCFlowGetExperimentInput(graphene.InputObjectType):
    experiment_id = graphene.String()


class QueryType(graphene.ObjectType):
    qcflow_get_experiment = graphene.Field(QCFlowGetExperimentResponse, input=QCFlowGetExperimentInput())
    qcflow_get_metric_history_bulk_interval = graphene.Field(QCFlowGetMetricHistoryBulkIntervalResponse, input=QCFlowGetMetricHistoryBulkIntervalInput())
    qcflow_get_run = graphene.Field(QCFlowGetRunResponse, input=QCFlowGetRunInput())
    qcflow_list_artifacts = graphene.Field(QCFlowListArtifactsResponse, input=QCFlowListArtifactsInput())
    qcflow_search_model_versions = graphene.Field(QCFlowSearchModelVersionsResponse, input=QCFlowSearchModelVersionsInput())

    def resolve_qcflow_get_experiment(self, info, input):
        input_dict = vars(input)
        request_message = qcflow.protos.service_pb2.GetExperiment()
        parse_dict(input_dict, request_message)
        return qcflow.server.handlers.get_experiment_impl(request_message)

    def resolve_qcflow_get_metric_history_bulk_interval(self, info, input):
        input_dict = vars(input)
        request_message = qcflow.protos.service_pb2.GetMetricHistoryBulkInterval()
        parse_dict(input_dict, request_message)
        return qcflow.server.handlers.get_metric_history_bulk_interval_impl(request_message)

    def resolve_qcflow_get_run(self, info, input):
        input_dict = vars(input)
        request_message = qcflow.protos.service_pb2.GetRun()
        parse_dict(input_dict, request_message)
        return qcflow.server.handlers.get_run_impl(request_message)

    def resolve_qcflow_list_artifacts(self, info, input):
        input_dict = vars(input)
        request_message = qcflow.protos.service_pb2.ListArtifacts()
        parse_dict(input_dict, request_message)
        return qcflow.server.handlers.list_artifacts_impl(request_message)

    def resolve_qcflow_search_model_versions(self, info, input):
        input_dict = vars(input)
        request_message = qcflow.protos.model_registry_pb2.SearchModelVersions()
        parse_dict(input_dict, request_message)
        return qcflow.server.handlers.search_model_versions_impl(request_message)


class MutationType(graphene.ObjectType):
    qcflow_search_datasets = graphene.Field(QCFlowSearchDatasetsResponse, input=QCFlowSearchDatasetsInput())
    qcflow_search_runs = graphene.Field(QCFlowSearchRunsResponse, input=QCFlowSearchRunsInput())

    def resolve_qcflow_search_datasets(self, info, input):
        input_dict = vars(input)
        request_message = qcflow.protos.service_pb2.SearchDatasets()
        parse_dict(input_dict, request_message)
        return qcflow.server.handlers.search_datasets_impl(request_message)

    def resolve_qcflow_search_runs(self, info, input):
        input_dict = vars(input)
        request_message = qcflow.protos.service_pb2.SearchRuns()
        parse_dict(input_dict, request_message)
        return qcflow.server.handlers.search_runs_impl(request_message)
