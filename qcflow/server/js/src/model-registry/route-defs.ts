import { createLazyRouteElement } from '../common/utils/RoutingUtils';

import { ModelRegistryRoutePaths } from './routes';

export const getRouteDefs = () => [
  {
    path: ModelRegistryRoutePaths.modelListPage,
    element: createLazyRouteElement(() => import('./components/ModelListPageWrapper')),
    pageId: 'qcflow.model-registry.model-list',
  },
  {
    path: ModelRegistryRoutePaths.modelPage,
    element: createLazyRouteElement(() => import('./components/ModelPage')),
    pageId: 'qcflow.model-registry.model-page',
  },
  {
    path: ModelRegistryRoutePaths.modelSubpage,
    element: createLazyRouteElement(() => import('./components/ModelPage')),
    pageId: 'qcflow.model-registry.model-page.subpage',
  },
  {
    path: ModelRegistryRoutePaths.modelSubpageRouteWithName,
    element: createLazyRouteElement(() => import('./components/ModelPage')),
    pageId: 'qcflow.model-registry.model-page.subpage.section',
  },
  {
    path: ModelRegistryRoutePaths.modelVersionPage,
    element: createLazyRouteElement(() => import('./components/ModelVersionPage')),
    pageId: 'qcflow.model-registry.model-version-page',
  },
  {
    path: ModelRegistryRoutePaths.compareModelVersionsPage,
    element: createLazyRouteElement(() => import('./components/CompareModelVersionsPage')),
    pageId: 'qcflow.model-registry.compare-model-versions',
  },
];
