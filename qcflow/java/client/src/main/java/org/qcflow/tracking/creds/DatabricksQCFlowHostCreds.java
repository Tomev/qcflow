package org.qcflow.tracking.creds;

/** Credentials to talk to a Databricks-hosted QCFlow server. */
public final class DatabricksQCFlowHostCreds extends BasicQCFlowHostCreds {

  public DatabricksQCFlowHostCreds(String host, String username, String password) {
    super(host, username, password);
  }

  public DatabricksQCFlowHostCreds(String host, String token) {
    super(host, token);
  }

  public DatabricksQCFlowHostCreds(
      String host,
      String username,
      String password,
      String token,
      boolean shouldIgnoreTlsVerification) {
    super(host, username, password, token, shouldIgnoreTlsVerification);
  }
}
