import { combineReducers } from 'redux';
import { ModelGatewayRouteLegacy, ModelGatewayRoute } from '../sdk/ModelGatewayService';
import { ModelGatewayRouteTask } from '../sdk/QCFlowEnums';
import { fulfilled, pending, rejected } from '../../common/utils/ActionUtils';

import type { AsyncAction, AsyncFulfilledAction } from '../../redux-types';
import type { SearchQCFlowDeploymentsModelRoutesAction } from '../actions/ModelGatewayActions';

export interface ModelGatewayReduxState {
  modelGatewayRoutesLegacy: Record<string, ModelGatewayRouteLegacy>;
  modelGatewayRoutesLoadingLegacy: boolean;
  modelGatewayRoutes: Record<string, ModelGatewayRoute>;
  modelGatewayRoutesLoading: {
    gatewayRoutesLoading?: boolean;
    endpointRoutesLoading?: boolean;
    deploymentRoutesLoading?: boolean;
    loading: boolean;
  };
}

export const modelGatewayRoutesLoading = (
  state = {
    gatewayRoutesLoading: false,
    endpointRoutesLoading: false,
    deploymentRoutesLoading: false,
    loading: false,
  },
  action: AsyncAction,
) => {
  switch (action.type) {
    case pending('SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES'):
      return { ...state, deploymentRoutesLoading: true, loading: true };
    case fulfilled('SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES'):
    case rejected('SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES'):
      return {
        ...state,
        deploymentRoutesLoading: false,
        loading: state.endpointRoutesLoading || state.gatewayRoutesLoading,
      };
  }
  return state;
};

type ModelGatewayReducerActions = AsyncFulfilledAction<SearchQCFlowDeploymentsModelRoutesAction>;
export const modelGatewayRoutes = (
  state: Record<string, ModelGatewayRoute> = {},
  { payload, type }: ModelGatewayReducerActions,
): Record<string, ModelGatewayRoute> => {
  const compatibleEndpointTypes = [ModelGatewayRouteTask.LLM_V1_COMPLETIONS, ModelGatewayRouteTask.LLM_V1_CHAT];
  switch (type) {
    case fulfilled('SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES'):
      if (!payload.endpoints) {
        return state;
      }
      const compatibleGatewayEndpoints = payload.endpoints.filter(
        ({ endpoint_type }) =>
          endpoint_type && compatibleEndpointTypes.includes(endpoint_type as ModelGatewayRouteTask),
      );
      return compatibleGatewayEndpoints.reduce((newState, deploymentEndpoint) => {
        return {
          ...newState,
          [`qcflow_deployment_endpoint:${deploymentEndpoint.name}`]: {
            type: 'qcflow_deployment_endpoint',
            key: `qcflow_deployment_endpoint:${deploymentEndpoint.name}`,
            name: deploymentEndpoint.name,
            qcflowDeployment: deploymentEndpoint,
            task: deploymentEndpoint.endpoint_type as ModelGatewayRouteTask,
          },
        };
      }, state);
  }
  return state;
};

export const modelGatewayReducer = combineReducers({
  modelGatewayRoutesLoading,
  modelGatewayRoutes,
});
