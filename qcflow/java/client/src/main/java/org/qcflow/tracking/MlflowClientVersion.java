package org.qcflow.tracking;

import java.io.InputStream;
import java.util.Properties;

import com.google.common.base.Supplier;
import com.google.common.base.Suppliers;

/** Returns the version of the QCFlow project this client was compiled against. */
public class QCFlowClientVersion {
  // To avoid extra disk IO during class loading (static initialization), we lazily read the
  // pom.properties file on first access and then cache the result to avoid future IO.
  private static Supplier<String> clientVersionSupplier = Suppliers.memoize(() -> {
    try {
      Properties p = new Properties();
      InputStream is = QCFlowClientVersion.class.getResourceAsStream(
        "/META-INF/maven/org.qcflow/qcflow-client/pom.properties");
      if (is == null) {
        return "";
      }
      p.load(is);
      return p.getProperty("version", "");
    } catch (Exception e) {
      return "";
    }
  });

  private QCFlowClientVersion() {}

  /** @return QCFlow client version (e.g., 0.9.1) or an empty string if detection fails. */
  public static String getClientVersion() {
    return clientVersionSupplier.get();
  }
}
