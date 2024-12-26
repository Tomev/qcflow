/**
 * NOTE: this code file was automatically migrated to TypeScript using ts-migrate and
 * may contain multiple `any` type annotations and `@ts-expect-error` directives.
 * If possible, please improve types while making changes to this file. If the type
 * annotations are already looking good, please remove this comment.
 */

/**
 * DO NOT EDIT!!!
 *
 * @NOTE(dli) 12-21-2016
 *   This file is generated. For now, it is a snapshot of the proto services as of
 *   Aug 1, 2018 3:42:41 PM. We will update the generation pipeline to actually
 *   place these generated objects in the correct location shortly.
 */
import { ModelTraceInfo, ModelTraceData } from '@databricks/web-shared/model-trace-explorer';
import { type ParsedQs, stringify as queryStringStringify } from 'qs';
import {
  deleteJson,
  fetchEndpoint,
  getBigIntJson,
  getJson,
  patchJson,
  postBigIntJson,
  postJson,
} from '../../common/utils/FetchUtils';
import { RunInfoEntity } from '../types';
import {
  transformGetExperimentResponse,
  transformGetRunResponse,
  transformSearchExperimentsResponse,
  transformSearchRunsResponse,
} from './FieldNameTransformers';

type CreateRunApiRequest = {
  experiment_id: string;
  start_time?: number;
  tags?: any;
  run_name?: string;
};

type GetCredentialsForLoggedModelArtifactReadResult = {
  credentials: {
    credential_info: {
      type: string;
      signed_uri: string;
      path: string;
    };
  }[];
};
const searchRunsPath = () => 'ajax-api/2.0/qcflow/runs/search';

export class QCFlowService {
  /**
   * Create a qcflow experiment
   */
  static createExperiment = (data: any) => postJson({ relativeUrl: 'ajax-api/2.0/qcflow/experiments/create', data });

  /**
   * Delete a qcflow experiment
   */
  static deleteExperiment = (data: any) => postJson({ relativeUrl: 'ajax-api/2.0/qcflow/experiments/delete', data });

  /**
   * Update a qcflow experiment
   */
  static updateExperiment = (data: any) => postJson({ relativeUrl: 'ajax-api/2.0/qcflow/experiments/update', data });

  /**
   * Search qcflow experiments
   */
  static searchExperiments = (data: any) =>
    getBigIntJson({ relativeUrl: 'ajax-api/2.0/qcflow/experiments/search', data }).then(
      transformSearchExperimentsResponse,
    );

  /**
   * Get qcflow experiment
   */
  static getExperiment = (data: any) =>
    getBigIntJson({ relativeUrl: 'ajax-api/2.0/qcflow/experiments/get', data }).then(transformGetExperimentResponse);

  /**
   * Get qcflow experiment by name
   */
  static getExperimentByName = (data: any) =>
    getBigIntJson({ relativeUrl: 'ajax-api/2.0/qcflow/experiments/get-by-name', data }).then(
      transformGetExperimentResponse,
    );

  /**
   * Create a qcflow experiment run
   */
  static createRun = (data: CreateRunApiRequest) =>
    postJson({ relativeUrl: 'ajax-api/2.0/qcflow/runs/create', data }) as Promise<{
      run: { info: RunInfoEntity };
    }>;

  /**
   * Delete a qcflow experiment run
   */
  static deleteRun = (data: any) => postJson({ relativeUrl: 'ajax-api/2.0/qcflow/runs/delete', data });

  /**
   * Search datasets used in experiments
   */
  static searchDatasets = (data: any) =>
    postJson({ relativeUrl: 'ajax-api/2.0/qcflow/experiments/search-datasets', data });

  /**
   * Restore a qcflow experiment run
   */
  static restoreRun = (data: any) => postJson({ relativeUrl: 'ajax-api/2.0/qcflow/runs/restore', data });

  /**
   * Update a qcflow experiment run
   */
  static updateRun = (data: any) => postJson({ relativeUrl: 'ajax-api/2.0/qcflow/runs/update', data });

  /**
   * Log qcflow experiment run metric
   */
  static logMetric = (data: any) => postJson({ relativeUrl: 'ajax-api/2.0/qcflow/runs/log-metric', data });

  /**
   * Log qcflow experiment run parameter
   */
  static logParam = (data: any) => postJson({ relativeUrl: 'ajax-api/2.0/qcflow/runs/log-parameter', data });

  /**
   * Get qcflow experiment run
   */
  static getRun = (data: any) =>
    getBigIntJson({ relativeUrl: 'ajax-api/2.0/qcflow/runs/get', data }).then(transformGetRunResponse);

  /**
   * Search qcflow experiment runs
   */
  static searchRuns = (data: any) =>
    postJson({ relativeUrl: searchRunsPath(), data }).then(transformSearchRunsResponse);

  /**
   * List model artifacts
   */
  static listArtifacts = (data: any) => getBigIntJson({ relativeUrl: 'ajax-api/2.0/qcflow/artifacts/list', data });

  /**
   * List model artifacts for logged models
   */
  static listArtifactsLoggedModel = ({ loggedModelId, path }: { loggedModelId: string; path: string }) =>
    getBigIntJson({
      relativeUrl: `ajax-api/2.0/qcflow/logged-models/${loggedModelId}/artifacts/directories`,
      data: path ? { artifact_directory_path: path } : {},
    });

  static getCredentialsForLoggedModelArtifactRead = ({
    loggedModelId,
    path,
  }: {
    loggedModelId: string;
    path: string;
  }) =>
    postBigIntJson({
      relativeUrl: `ajax-api/2.0/qcflow/logged-models/${loggedModelId}/artifacts/credentials-for-download`,
      data: {
        paths: [path],
      },
    }) as Promise<GetCredentialsForLoggedModelArtifactReadResult>;

  /**
   * Get metric history
   */
  static getMetricHistory = (data: any) =>
    getBigIntJson({ relativeUrl: 'ajax-api/2.0/qcflow/metrics/get-history', data });

  /**
   * Set qcflow experiment run tag
   */
  static setTag = (data: any) => postJson({ relativeUrl: 'ajax-api/2.0/qcflow/runs/set-tag', data });

  /**
   * Delete qcflow experiment run tag
   */
  static deleteTag = (data: any) => postJson({ relativeUrl: 'ajax-api/2.0/qcflow/runs/delete-tag', data });

  /**
   * Set qcflow experiment tag
   */
  static setExperimentTag = (data: any) =>
    postJson({ relativeUrl: 'ajax-api/2.0/qcflow/experiments/set-experiment-tag', data });

  /**
   * Create prompt engineering run
   */
  static createPromptLabRun = (data: {
    experiment_id: string;
    tags?: { key: string; value: string }[];
    prompt_template: string;
    prompt_parameters: { key: string; value: string }[];
    model_route: string;
    model_parameters: { key: string; value: string | number | undefined }[];
    model_output_parameters: { key: string; value: string | number }[];
    model_output: string;
  }) => postJson({ relativeUrl: 'ajax-api/2.0/qcflow/runs/create-promptlab-run', data });

  /**
   * Proxy post request to gateway server
   */
  static gatewayProxyPost = (data: { gateway_path: string; json_data: any }, error?: any) =>
    postJson({ relativeUrl: 'ajax-api/2.0/qcflow/gateway-proxy', data, error });

  /**
   * Proxy get request to gateway server
   */
  static gatewayProxyGet = (data: { gateway_path: string; json_data?: any }) =>
    getJson({ relativeUrl: 'ajax-api/2.0/qcflow/gateway-proxy', data });

  /**
   * Traces API: get traces list
   */
  static getExperimentTraces = (experimentIds: string[], orderBy: string, pageToken?: string, filterString = '') => {
    type GetExperimentTracesResponse = {
      traces?: ModelTraceInfo[];
      next_page_token?: string;
      prev_page_token?: string;
    };

    // usually we send array data via POST request, but since this
    // is a GET, we need to treat it specially. we use `qs` to
    // serialize the array into a query string which the backend
    // can handle. this is similar to the approach taken in the
    // GetMetricHistoryBulkInterval API.
    const queryString = queryStringStringify(
      {
        experiment_ids: experimentIds,
        order_by: orderBy,
        page_token: pageToken,
        filter: filterString,
      },
      { arrayFormat: 'repeat' },
    );

    return fetchEndpoint({
      relativeUrl: `ajax-api/2.0/qcflow/traces?${queryString}`,
    }) as Promise<GetExperimentTracesResponse>;
  };

  static getExperimentTraceInfo = (requestId: string) => {
    type GetExperimentTraceInfoResponse = {
      trace_info?: ModelTraceInfo;
    };

    return getJson({
      relativeUrl: `ajax-api/2.0/qcflow/traces/${requestId}/info`,
    }) as Promise<GetExperimentTraceInfoResponse>;
  };

  /**
   * Traces API: get credentials for data download
   */
  static getExperimentTraceData = <T = ModelTraceData>(traceRequestId: string) => {
    return getJson({
      relativeUrl: `ajax-api/2.0/qcflow/get-trace-artifact`,
      data: {
        request_id: traceRequestId,
      },
    }) as Promise<T>;
  };

  /**
   * Traces API: set trace tag
   */
  static setExperimentTraceTag = (traceRequestId: string, key: string, value: string) =>
    patchJson({
      relativeUrl: `ajax-api/2.0/qcflow/traces/${traceRequestId}/tags`,
      data: {
        key,
        value,
      },
    });

  /**
   * Traces API: delete trace tag
   */
  static deleteExperimentTraceTag = (traceRequestId: string, key: string) =>
    deleteJson({
      relativeUrl: `ajax-api/2.0/qcflow/traces/${traceRequestId}/tags`,
      data: {
        key,
      },
    });

  static deleteTraces = (experimentId: string, traceRequestIds: string[]) =>
    postJson({
      relativeUrl: `ajax-api/2.0/qcflow/traces/delete-traces`,
      data: {
        experiment_id: experimentId,
        request_ids: traceRequestIds,
      },
    }) as Promise<{ traces_deleted: number }>;
}
