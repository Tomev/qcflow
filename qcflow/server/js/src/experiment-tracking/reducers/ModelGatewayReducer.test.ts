import { fulfilled, pending } from '../../common/utils/ActionUtils';
import { AsyncAction, AsyncFulfilledAction } from '../../redux-types';
import { QCFlowDeploymentsEndpoint } from '../sdk/ModelGatewayService';
import { SearchQCFlowDeploymentsModelRoutesAction } from '../actions/ModelGatewayActions';
import { ModelGatewayRouteTask } from '../sdk/QCFlowEnums';
import { modelGatewayReducer } from './ModelGatewayReducer';

describe('modelGatewayReducer - QCFlow deployments endpoints', () => {
  const emptyState: ReturnType<typeof modelGatewayReducer> = {
    modelGatewayRoutes: {},
    modelGatewayRoutesLoading: {
      deploymentRoutesLoading: false,
      endpointRoutesLoading: false,
      gatewayRoutesLoading: false,
      loading: false,
    },
  };

  const MOCK_QCFLOW_DEPLOYMENTS_RESPONSE: Partial<QCFlowDeploymentsEndpoint>[] = [
    {
      endpoint_type: ModelGatewayRouteTask.LLM_V1_CHAT,
      name: 'test-qcflow-deployment-endpoint-chat',
      endpoint_url: 'http://deployment.server/endpoint-url',
      model: {
        name: 'mpt-3.5',
        provider: 'mosaic',
      },
    },
    {
      endpoint_type: ModelGatewayRouteTask.LLM_V1_EMBEDDINGS,
      name: 'test-qcflow-deployment-endpoint-embeddingss',
      endpoint_url: 'http://deployment.server/endpoint-url',
      model: {
        name: 'mpt-3.5',
        provider: 'mosaic',
      },
    },
  ];

  const mockFulfilledSearchDeploymentsAction = (
    endpoints: any,
  ): AsyncFulfilledAction<SearchQCFlowDeploymentsModelRoutesAction> => ({
    type: fulfilled('SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES'),
    payload: { endpoints },
  });

  const mockPendingSearchDeploymentsAction = (): AsyncAction => ({
    type: pending('SEARCH_QCFLOW_DEPLOYMENTS_MODEL_ROUTES'),
    payload: Promise.resolve(),
  });

  it('gateway routes are correctly populated by search action', () => {
    let state = emptyState;
    // Start searching for routes
    state = modelGatewayReducer(state, mockPendingSearchDeploymentsAction());
    expect(state.modelGatewayRoutesLoading.deploymentRoutesLoading).toEqual(true);
    expect(state.modelGatewayRoutesLoading.loading).toEqual(true);

    // Search and retrieve 2 model routes
    state = modelGatewayReducer(state, mockFulfilledSearchDeploymentsAction(MOCK_QCFLOW_DEPLOYMENTS_RESPONSE));

    expect(state.modelGatewayRoutesLoading.deploymentRoutesLoading).toEqual(false);
    expect(state.modelGatewayRoutesLoading.loading).toEqual(false);
    expect(state.modelGatewayRoutes['qcflow_deployment_endpoint:test-qcflow-deployment-endpoint-chat'].type).toEqual(
      'qcflow_deployment_endpoint',
    );
    expect(state.modelGatewayRoutes['qcflow_deployment_endpoint:test-qcflow-deployment-endpoint-chat'].name).toEqual(
      'test-qcflow-deployment-endpoint-chat',
    );
    expect(
      state.modelGatewayRoutes['qcflow_deployment_endpoint:test-qcflow-deployment-endpoint-chat'].qcflowDeployment,
    ).toEqual(MOCK_QCFLOW_DEPLOYMENTS_RESPONSE[0]);

    // We ignore embeddings endpoints for now
    expect(
      state.modelGatewayRoutes['qcflow_deployment_endpoint:test-qcflow-deployment-endpoint-embeddings'],
    ).toBeUndefined();
  });
});
