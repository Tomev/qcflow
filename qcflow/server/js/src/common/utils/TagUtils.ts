/**
 * NOTE: this code file was automatically migrated to TypeScript using ts-migrate and
 * may contain multiple `any` type annotations and `@ts-expect-error` directives.
 * If possible, please improve types while making changes to this file. If the type
 * annotations are already looking good, please remove this comment.
 */

import { QCFLOW_LOGGED_ARTIFACTS_TAG } from '@qcflow/qcflow/src/experiment-tracking/constants';
import Utils from './Utils';
import { KeyValueEntity, RunLoggedArtifactType } from '@qcflow/qcflow/src/experiment-tracking/types';

export const QCFLOW_INTERNAL_PREFIX = 'qcflow.';

export const isUserFacingTag = (tagKey: string) => !tagKey.startsWith(QCFLOW_INTERNAL_PREFIX);

export const getLoggedModelPathsFromTags = (runTags: Record<string, KeyValueEntity>) => {
  const models = Utils.getLoggedModelsFromTags(runTags);
  return models ? models.map((model) => (model as any).artifactPath) : [];
};

// Safe JSON.parse that returns undefined instead of throwing an error
export const parseJSONSafe = (json: string) => {
  try {
    return JSON.parse(json);
  } catch (e) {
    return undefined;
  }
};

export const getLoggedTablesFromTags = (runTags: any) => {
  const artifactsTags = runTags[QCFLOW_LOGGED_ARTIFACTS_TAG];
  if (artifactsTags) {
    const artifacts = parseJSONSafe(artifactsTags.value);
    if (artifacts) {
      return artifacts
        .filter((artifact: any) => artifact.type === RunLoggedArtifactType.TABLE)
        .map((artifact: any) => artifact.path);
    }
  }
  return [];
};
