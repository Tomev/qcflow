import React, { useMemo } from 'react';
import { LegacySkeleton } from '@databricks/design-system';

import ErrorModal from './experiment-tracking/components/modals/ErrorModal';
import AppErrorBoundary from './common/components/error-boundaries/AppErrorBoundary';
import { HashRouter, Route, Routes, createLazyRouteElement } from './common/utils/RoutingUtils';
import { QCFlowHeader } from './common/components/QCFlowHeader';

// Route definition imports:
import { getRouteDefs as getExperimentTrackingRouteDefs } from './experiment-tracking/route-defs';
import { getRouteDefs as getModelRegistryRouteDefs } from './model-registry/route-defs';
import { getRouteDefs as getCommonRouteDefs } from './common/route-defs';
import { useInitializeExperimentRunColors } from './experiment-tracking/components/experiment-page/hooks/useExperimentRunColor';

/**
 * This is the QCFlow default entry/landing route.
 */
const landingRoute = {
  path: '/',
  element: createLazyRouteElement(() => import('./experiment-tracking/components/HomePage')),
  pageId: 'qcflow.experiments.list',
};

export const QCFlowRouter = ({
  isDarkTheme,
  setIsDarkTheme,
}: {
  isDarkTheme?: boolean;
  setIsDarkTheme?: (isDarkTheme: boolean) => void;
}) => {
  // eslint-disable-next-line react-hooks/rules-of-hooks
  useInitializeExperimentRunColors();

  // eslint-disable-next-line react-hooks/rules-of-hooks
  const routes = useMemo(
    () => [...getExperimentTrackingRouteDefs(), ...getModelRegistryRouteDefs(), landingRoute, ...getCommonRouteDefs()],
    [],
  );
  return (
    <>
      <ErrorModal />
      <HashRouter>
        <AppErrorBoundary>
          <QCFlowHeader isDarkTheme={isDarkTheme} setIsDarkTheme={setIsDarkTheme} />
          <React.Suspense fallback={<LegacySkeleton />}>
            <Routes>
              {routes.map(({ element, pageId, path }) => (
                <Route key={pageId} path={path} element={element} />
              ))}
            </Routes>
          </React.Suspense>
        </AppErrorBoundary>
      </HashRouter>
    </>
  );
};
