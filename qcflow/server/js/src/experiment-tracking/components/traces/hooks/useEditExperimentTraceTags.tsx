import { type ModelTraceInfo } from '@databricks/web-shared/model-trace-explorer';
import { useEditKeyValueTagsModal } from '../../../../common/hooks/useEditKeyValueTagsModal';
import { QCFlowService } from '../../../sdk/QCFlowService';
import { KeyValueEntity } from '../../../types';
import { useCallback } from 'react';
import { QCFLOW_INTERNAL_PREFIX } from '../../../../common/utils/TagUtils';

type EditedModelTrace = {
  traceRequestId: string;
  tags: KeyValueEntity[];
};

export const useEditExperimentTraceTags = ({
  onSuccess,
  existingTagKeys = [],
}: {
  onSuccess?: () => void;
  existingTagKeys?: string[];
}) => {
  const { showEditTagsModal, EditTagsModal } = useEditKeyValueTagsModal<EditedModelTrace>({
    saveTagsHandler: async (editedEntity, existingTags, newTags) => {
      if (!editedEntity.traceRequestId) {
        return;
      }
      const requestId = editedEntity.traceRequestId;
      // First, determine new tags to be added
      const addedOrModifiedTags = newTags.filter(
        ({ key: newTagKey, value: newTagValue }) =>
          !existingTags.some(
            ({ key: existingTagKey, value: existingTagValue }) =>
              existingTagKey === newTagKey && newTagValue === existingTagValue,
          ),
      );

      // Next, determine those to be deleted
      const deletedTags = existingTags.filter(
        ({ key: existingTagKey }) => !newTags.some(({ key: newTagKey }) => existingTagKey === newTagKey),
      );

      // Fire all requests at once
      const updateRequests = Promise.all([
        ...addedOrModifiedTags.map(({ key, value }) => QCFlowService.setExperimentTraceTag(requestId, key, value)),
        ...deletedTags.map(({ key }) => QCFlowService.deleteExperimentTraceTag(requestId, key)),
      ]);

      return updateRequests;
    },
    valueRequired: true,
    allAvailableTags: existingTagKeys.filter((tagKey) => tagKey && !tagKey.startsWith(QCFLOW_INTERNAL_PREFIX)),
    onSuccess: onSuccess,
  });

  const showEditTagsModalForTrace = useCallback(
    (trace: ModelTraceInfo) => {
      if (!trace.request_id) {
        return;
      }
      const visibleTags = trace.tags?.filter(({ key }) => key && !key.startsWith(QCFLOW_INTERNAL_PREFIX)) || [];
      showEditTagsModal({
        traceRequestId: trace.request_id,
        tags: visibleTags || [],
      });
    },
    [showEditTagsModal],
  );

  return {
    showEditTagsModalForTrace,
    EditTagsModal,
  };
};
