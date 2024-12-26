package org.qcflow.tracking.creds;

/** Provides a dynamic, refreshable set of QCFlowHostCreds. */
public interface QCFlowHostCredsProvider {

  /** Returns a valid QCFlowHostCreds. This may be cached. */
  QCFlowHostCreds getHostCreds();

  /** Refreshes the underlying credentials. May be a no-op. */
  void refresh();
}
