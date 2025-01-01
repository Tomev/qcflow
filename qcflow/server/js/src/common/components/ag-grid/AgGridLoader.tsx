import type { AgGridReactProps, AgReactUiProps } from '@ag-grid-community/react';
import { Spinner } from '@databricks/design-system';
import React from 'react';

const QCFlowAgGridImpl = React.lazy(() => import('./AgGrid'));

/**
 * A simple loader that will lazily load QCFlow's ag grid implementation.
 * Extracted to a separate module for testing purposes.
 */
export const QCFlowAgGridLoader = (props: AgGridReactProps | AgReactUiProps) => (
  <React.Suspense
    fallback={
      <div
        css={(cssTheme) => ({
          display: 'flex',
          justifyContent: 'center',
          margin: cssTheme.spacing.md,
        })}
      >
        <Spinner />
      </div>
    }
  >
    <QCFlowAgGridImpl {...props} />
  </React.Suspense>
);
