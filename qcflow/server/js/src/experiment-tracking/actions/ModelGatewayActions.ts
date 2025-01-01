import { QCFlowService } from '@qcflow/qcflow/src/experiment-tracking/sdk/QCFlowService';
import { getUUID } from '../../common/utils/ActionUtils';
import type { AsyncAction } from '../../redux-types';
import {
  ModelGatewayQueryPayload,
  ModelGatewayRoute,
  ModelGatewayRouteLegacy,
  ModelGatewayService,
  SearchQCFlowDeploymentsModelRoutesResponse,
} from '../sdk/ModelGatewayService';

export const SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES = 'SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES';

export interface SearchQCFlowDeploymentsModelRoutesAction
  extends AsyncAction<SearchQCFlowDeploymentsModelRoutesResponse> {
  type: 'SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES';
}

export const searchQCFlowDeploymentsRoutesApi = (filter?: string): SearchQCFlowDeploymentsModelRoutesAction => ({
  type: SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES,
  payload: QCFlowService.gatewayProxyGet({
    gateway_path: 'api/2.0/endpoints/',
  }) as Promise<SearchQCFlowDeploymentsModelRoutesResponse>,
  meta: { id: getUUID() },
});
export const QUERY_QCFLOW_DEPLOYMENTS_ROUTE_API = 'QUERY_QCFLOW_DEPLOYMENTS_ROUTE_API';
export const queryQCFlowDeploymentsRouteApi = (route: ModelGatewayRoute, data: ModelGatewayQueryPayload) => {
  return {
    type: QUERY_QCFLOW_DEPLOYMENTS_ROUTE_API,
    payload: ModelGatewayService.queryQCFlowDeploymentEndpointRoute(route, data),
    meta: { id: getUUID(), startTime: performance.now() },
  };
};
