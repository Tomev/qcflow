import PageNotFoundView from './components/PageNotFoundView';
import { createQCFlowRoutePath, createRouteElement } from './utils/RoutingUtils';

/**
 * Common route definitions. For the time being it's 404 page only.
 */
export const getRouteDefs = () => [
  {
    path: createQCFlowRoutePath('/*'),
    element: createRouteElement(PageNotFoundView),
    pageId: 'qcflow.common.not-found',
  },
];
