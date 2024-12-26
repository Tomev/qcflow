package org.qcflow.tracking.creds;

/** A static hostname and optional credentials to talk to an QCFlow server. */
public class BasicQCFlowHostCreds implements QCFlowHostCreds, QCFlowHostCredsProvider {
  private String host;
  private String username;
  private String password;
  private String token;
  private boolean shouldIgnoreTlsVerification;

  public BasicQCFlowHostCreds(String host) {
    this.host = host;
  }

  public BasicQCFlowHostCreds(String host, String username, String password) {
    this.host = host;
    this.username = username;
    this.password = password;
  }

  public BasicQCFlowHostCreds(String host, String token) {
    this.host = host;
    this.token = token;
  }

  public BasicQCFlowHostCreds(
      String host,
      String username,
      String password,
      String token,
      boolean shouldIgnoreTlsVerification) {
    this.host = host;
    this.username = username;
    this.password = password;
    this.token = token;
    this.shouldIgnoreTlsVerification = shouldIgnoreTlsVerification;
  }

  @Override
  public String getHost() {
    return host;
  }

  @Override
  public String getUsername() {
    return username;
  }

  @Override
  public String getPassword() {
    return password;
  }

  @Override
  public String getToken() {
    return token;
  }

  @Override
  public boolean shouldIgnoreTlsVerification() {
    return shouldIgnoreTlsVerification;
  }

  @Override
  public QCFlowHostCreds getHostCreds() {
    return this;
  }

  @Override
  public void refresh() {
    // no-op
  }
}
