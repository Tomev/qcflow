import { createLazyRouteElement } from '../common/utils/RoutingUtils';

import { RoutePaths } from './routes';
export const getRouteDefs = () => [
  {
    path: RoutePaths.experimentPage,
    element: createLazyRouteElement(() => import(/* webpackChunkName: "experimentPage" */ './components/HomePage')),
    pageId: 'qcflow.experiment.details',
  },
  {
    path: RoutePaths.experimentPageSearch,
    element: createLazyRouteElement(() => import(/* webpackChunkName: "experimentPage" */ './components/HomePage')),
    pageId: 'qcflow.experiment.details.search',
  },
  {
    path: RoutePaths.compareExperimentsSearch,
    element: createLazyRouteElement(() => import(/* webpackChunkName: "experimentPage" */ './components/HomePage')),
    pageId: 'qcflow.experiment.compare',
  },
  {
    path: RoutePaths.runPageWithTab,
    element: createLazyRouteElement(() => import('./components/run-page/RunPage')),
    pageId: 'qcflow.experiment.run.details',
  },
  {
    path: RoutePaths.runPageDirect,
    element: createLazyRouteElement(() => import('./components/DirectRunPage')),
    pageId: 'qcflow.experiment.run.details.direct',
  },
  {
    path: RoutePaths.compareRuns,
    element: createLazyRouteElement(() => import('./components/CompareRunPage')),
    pageId: 'qcflow.experiment.run.compare',
  },
  {
    path: RoutePaths.metricPage,
    element: createLazyRouteElement(() => import('./components/MetricPage')),
    pageId: 'qcflow.metric.details',
  },
];
