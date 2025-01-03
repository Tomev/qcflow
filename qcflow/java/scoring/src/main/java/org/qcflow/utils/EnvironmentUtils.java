package org.qcflow.utils;

/** Utilities for reading from / writing to the system environment */
public class EnvironmentUtils {
  public static int getIntegerValue(String varName, int defaultValue) {
    String rawValue = System.getenv(varName);
    if (rawValue == null) {
      return defaultValue;
    } else {
      return Integer.valueOf(rawValue);
    }
  }
}
