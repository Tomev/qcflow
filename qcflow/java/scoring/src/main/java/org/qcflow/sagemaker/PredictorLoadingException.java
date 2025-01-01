package org.qcflow.sagemaker;

/**
 * An exception indicating a failure during the process of creating a {@link
 * org.qcflow.sagemaker.Predictor} from an QCFlow model
 */
public class PredictorLoadingException extends RuntimeException {
  /**
   * Constructs an exception
   *
   * @param message The user-readable error message associated with this exception
   */
  public PredictorLoadingException(String message) {
    super(message);
  }

  /**
   * Constructs an exception with contents from a causal exception
   *
   * @param message The user-readable error message associated with this exception
   * @param ex The causal exception to include in the PredictorLoadingException
   */
  public PredictorLoadingException(String message, Exception ex) {
    super(message, ex);
  }
}
