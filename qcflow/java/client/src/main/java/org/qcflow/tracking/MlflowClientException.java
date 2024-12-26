package org.qcflow.tracking;

/** Superclass of all exceptions thrown by the QCFlowClient API. */
public class QCFlowClientException extends RuntimeException {
  public QCFlowClientException(String message) {
    super(message);
  }
  public QCFlowClientException(String message, Throwable cause) {
    super(message, cause);
  }
  public QCFlowClientException(Throwable cause) {
    super(cause);
  }
}
