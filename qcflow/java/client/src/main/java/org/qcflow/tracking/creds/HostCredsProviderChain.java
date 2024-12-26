package org.qcflow.tracking.creds;

import java.util.ArrayList;
import java.util.Arrays;
import java.util.List;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.qcflow.tracking.QCFlowClientException;

public class HostCredsProviderChain implements QCFlowHostCredsProvider {
  private static final Logger logger = LoggerFactory.getLogger(HostCredsProviderChain.class);

  private final List<QCFlowHostCredsProvider> hostCredsProviders = new ArrayList<>();

  public HostCredsProviderChain(QCFlowHostCredsProvider... hostCredsProviders) {
    this.hostCredsProviders.addAll(Arrays.asList(hostCredsProviders));
  }

  @Override
  public QCFlowHostCreds getHostCreds() {
    List<String> exceptionMessages = new ArrayList<>();
    for (QCFlowHostCredsProvider provider : hostCredsProviders) {
      try {
        QCFlowHostCreds hostCreds = provider.getHostCreds();

        if (hostCreds != null && hostCreds.getHost() != null) {
          logger.debug("Loading credentials from " + provider.toString());
          return hostCreds;
        }
      } catch (Exception e) {
        String message = provider + ": " + e.getMessage();
        logger.debug("Unable to load credentials from " + message);
        exceptionMessages.add(message);
      }
    }
    throw new QCFlowClientException("Unable to load QCFlow Host/Credentials from any provider in" +
      " the chain: " + exceptionMessages);
  }

  @Override
  public void refresh() {
    for (QCFlowHostCredsProvider provider : hostCredsProviders) {
      provider.refresh();
    }
  }
}