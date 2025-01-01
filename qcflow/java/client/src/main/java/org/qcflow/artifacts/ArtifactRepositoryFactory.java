package org.qcflow.artifacts;

import java.net.URI;

import org.qcflow.tracking.creds.QCFlowHostCredsProvider;

public class ArtifactRepositoryFactory {
  private final QCFlowHostCredsProvider hostCredsProvider;

  public ArtifactRepositoryFactory(QCFlowHostCredsProvider hostCredsProvider) {
    this.hostCredsProvider = hostCredsProvider;
  }

  public ArtifactRepository getArtifactRepository(URI baseArtifactUri, String runId) {
    return new CliBasedArtifactRepository(baseArtifactUri.toString(), runId, hostCredsProvider);
  }
}
