package org.qcflow;

/** Interface for exposing information about an QCFlow model flavor. */
public interface Flavor {
  /** @return The name of the model flavor */
  String getName();

  /**
   * @return The relative path to flavor-specific model data. This path is relative to the root
   *     directory of an QCFlow model
   */
  String getModelDataPath();
}
