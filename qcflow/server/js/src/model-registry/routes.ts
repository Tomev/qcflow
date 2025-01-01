import { createQCFlowRoutePath, generatePath } from '../common/utils/RoutingUtils';

// Route path definitions (used in defining route elements)
export class ModelRegistryRoutePaths {
  static get modelListPage() {
    return createQCFlowRoutePath('/models');
  }
  static get modelPage() {
    return createQCFlowRoutePath('/models/:modelName');
  }
  static get modelSubpage() {
    return createQCFlowRoutePath('/models/:modelName/:subpage');
  }
  static get modelSubpageRouteWithName() {
    return createQCFlowRoutePath('/models/:modelName/:subpage/:name');
  }
  static get modelVersionPage() {
    return createQCFlowRoutePath('/models/:modelName/versions/:version');
  }
  static get compareModelVersionsPage() {
    return createQCFlowRoutePath('/compare-model-versions');
  }
  static get createModel() {
    return createQCFlowRoutePath('/createModel');
  }
}

// Concrete routes and functions for generating parametrized paths
export class ModelRegistryRoutes {
  static get modelListPageRoute() {
    return ModelRegistryRoutePaths.modelListPage;
  }
  static getModelPageRoute(modelName: string) {
    return generatePath(ModelRegistryRoutePaths.modelPage, {
      modelName: encodeURIComponent(modelName),
    });
  }
  static getModelPageServingRoute(modelName: string) {
    return generatePath(ModelRegistryRoutePaths.modelSubpage, {
      modelName: encodeURIComponent(modelName),
      subpage: PANES.SERVING,
    });
  }
  static getModelVersionPageRoute(modelName: string, version: string) {
    return generatePath(ModelRegistryRoutePaths.modelVersionPage, {
      modelName: encodeURIComponent(modelName),
      version,
    });
  }
  static getCompareModelVersionsPageRoute(modelName: string, runsToVersions: Record<string, string>) {
    const path = generatePath(ModelRegistryRoutePaths.compareModelVersionsPage);
    const query =
      `?name=${JSON.stringify(encodeURIComponent(modelName))}` +
      `&runs=${JSON.stringify(runsToVersions, (_, v) => (v === undefined ? null : v))}`;

    return [path, query].join('');
  }
}

export const PANES = Object.freeze({
  DETAILS: 'details',
  SERVING: 'serving',
});
