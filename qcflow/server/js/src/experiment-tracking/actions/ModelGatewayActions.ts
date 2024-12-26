import { MlflowService } from '@qcflow/qcflow/src/experiment-tracking/sdk/MlflowService';
import { getUUID } from '../../common/utils/ActionUtils';
import type { AsyncAction } from '../../redux-types';
import {
  ModelGatewayQueryPayload,
  ModelGatewayRoute,
  ModelGatewayRouteLegacy,
  ModelGatewayService,
  SearchMlflowDeploymentsModelRoutesResponse,
} from '../sdk/ModelGatewayService';

export const SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES = 'SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES';

export interface SearchMlflowDeploymentsModelRoutesAction
  extends AsyncAction<SearchMlflowDeploymentsModelRoutesResponse> {
  type: 'SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES';
}

export const searchMlflowDeploymentsRoutesApi = (filter?: string): SearchMlflowDeploymentsModelRoutesAction => ({
  type: SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES,
  payload: MlflowService.gatewayProxyGet({
    gateway_path: 'api/2.0/endpoints/',
  }) as Promise<SearchMlflowDeploymentsModelRoutesResponse>,
  meta: { id: getUUID() },
});
export const QUERY_QCFLOW_DEPLOYMENTS_ROUTE_API = 'QUERY_QCFLOW_DEPLOYMENTS_ROUTE_API';
export const queryMlflowDeploymentsRouteApi = (route: ModelGatewayRoute, data: ModelGatewayQueryPayload) => {
  return {
    type: QUERY_QCFLOW_DEPLOYMENTS_ROUTE_API,
    payload: ModelGatewayService.queryQCFlowDeploymentEndpointRoute(route, data),
    meta: { id: getUUID(), startTime: performance.now() },
  };
};
