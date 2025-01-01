package org.qcflow.tracking.creds;

abstract class DatabricksHostCredsProvider implements QCFlowHostCredsProvider {

  @Override
  public abstract DatabricksQCFlowHostCreds getHostCreds();

  @Override
  public abstract void refresh();

}
