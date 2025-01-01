package org.qcflow;


/** Provides test resources in the org/qcflow test resources directory */
public class QCFlowRootResourceProvider {
  /**
   * @param relativePath The path to the requested resource, relative to the `org/qcflow` test
   *     resources directory
   * @return The absolute path to the requested resource
   */
  public static String getResourcePath(String relativePath) {
    return QCFlowRootResourceProvider.class.getResource(relativePath).getFile();
  }
}
