package org.qcflow.sagemaker;

/** Exception indicating a problem with a serialized MLeap schema */
public class InvalidSchemaException extends RuntimeException {
  InvalidSchemaException(String message) {
    super(message);
  }
}
