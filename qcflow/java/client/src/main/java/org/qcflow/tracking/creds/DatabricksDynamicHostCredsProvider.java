package org.qcflow.tracking.creds;

import java.util.Map;

import com.google.common.annotations.VisibleForTesting;
import org.qcflow.tracking.utils.DatabricksContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

public class DatabricksDynamicHostCredsProvider extends DatabricksHostCredsProvider {
  private static final Logger logger = LoggerFactory.getLogger(
    DatabricksDynamicHostCredsProvider.class);

  private final Map<String, String> configProvider;

  private DatabricksDynamicHostCredsProvider(Map<String, String> configProvider) {
    this.configProvider = configProvider;
  }

  public static DatabricksDynamicHostCredsProvider createIfAvailable() {
    return createIfAvailable(DatabricksContext.CONFIG_PROVIDER_CLASS_NAME);
  }

  @VisibleForTesting
  static DatabricksDynamicHostCredsProvider createIfAvailable(String className) {
    Map<String, String> configProvider =
      DatabricksContext.getConfigProviderIfAvailable(className);
    if (configProvider == null) {
      return null;
    }
    return new DatabricksDynamicHostCredsProvider(configProvider);
  }

  @Override
  public DatabricksQCFlowHostCreds getHostCreds() {
    return new DatabricksQCFlowHostCreds(
      configProvider.get("host"),
      configProvider.get("username"),
      configProvider.get("password"),
      configProvider.get("token"),
      "true".equals(configProvider.get("shouldIgnoreTlsVerification"))
    );
  }

  @Override
  public void refresh() {
    // no-op
  }
}
