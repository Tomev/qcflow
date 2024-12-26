import { ModelGatewayService } from './ModelGatewayService';
import { ModelGatewayRouteTask } from './QCFlowEnums';
import { fetchEndpoint } from '../../common/utils/FetchUtils';
import { QCFlowService } from './QCFlowService';

jest.mock('../../common/utils/FetchUtils', () => ({
  ...jest.requireActual('../../common/utils/FetchUtils'),
  fetchEndpoint: jest.fn(),
}));

describe('ModelGatewayService', () => {
  beforeEach(() => {
    jest
      .spyOn(QCFlowService, 'gatewayProxyPost')
      .mockResolvedValue({ choices: [{ message: { content: 'output text' } }], usage: {} });
  });
  afterEach(() => {
    jest.clearAllMocks();
  });

  test('Creates a request call to the QCFlow deployments model route', async () => {
    const result = await ModelGatewayService.queryModelGatewayRoute(
      {
        name: 'chat_route',
        key: 'qcflow_deployment_endpoint:test-qcflow-deployment-endpoint-chat',
        task: ModelGatewayRouteTask.LLM_V1_CHAT,
        type: 'qcflow_deployment_endpoint',
        qcflowDeployment: {
          endpoint_type: ModelGatewayRouteTask.LLM_V1_CHAT,
          endpoint_url: '/endpoint-url',
          model: {
            name: 'mpt-7b',
            provider: 'mosaic',
          },
          name: 'test-qcflow-deployment-endpoint-chat',
        },
      },
      { inputText: 'input text', parameters: { temperature: 0.5, max_tokens: 50 } },
    );

    expect(QCFlowService.gatewayProxyPost).toBeCalledWith(
      expect.objectContaining({
        gateway_path: 'endpoint-url',
        json_data: { messages: [{ content: 'input text', role: 'user' }], temperature: 0.5, max_tokens: 50 },
      }),
    );

    expect(result).toEqual(
      expect.objectContaining({
        text: 'output text',
      }),
    );
  });

  test('Throws when task is not supported', async () => {
    try {
      await ModelGatewayService.queryModelGatewayRoute(
        {
          name: 'embeddings_route',
          key: 'qcflow_deployment_endpoint:test-qcflow-deployment-endpoint-embeddings',
          task: ModelGatewayRouteTask.LLM_V1_EMBEDDINGS,
          type: 'qcflow_deployment_endpoint',
          qcflowDeployment: {
            endpoint_type: ModelGatewayRouteTask.LLM_V1_EMBEDDINGS,
            endpoint_url: '/endpoint-url',
            model: {
              name: 'mpt-7b',
              provider: 'mosaic',
            },
            name: 'test-qcflow-deployment-endpoint-embeddings',
          },
        },
        { inputText: 'input text', parameters: { temperature: 0.5, max_tokens: 50 } },
      );
    } catch (e: any) {
      expect(e.message).toMatch(/Unsupported served LLM model task/);
    }
  });

  test('Throws when route type is not supported', async () => {
    try {
      await ModelGatewayService.queryModelGatewayRoute(
        {
          type: 'some-unsupported-type',
          name: 'completions_route',
        } as any,
        { inputText: 'input text', parameters: { temperature: 0.5, max_tokens: 50 } },
      );
    } catch (e: any) {
      expect(e.message).toMatch(/Unknown route type/);
    }
  });
});
