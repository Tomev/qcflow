package org.qcflow;

import org.junit.Assert;
import org.junit.Test;
import org.qcflow.mleap.MLeapLoader;
import org.qcflow.sagemaker.Predictor;
import org.qcflow.sagemaker.PredictorLoadingException;

/** Unit tests for deserializing QCFlow models as generic {@link Predictor} objects for inference */
public class LoaderModuleTest {
  @Test
  public void testMLeapLoaderModuleDeserializesValidMLeapModelAsPredictor() {
    String modelPath = QCFlowRootResourceProvider.getResourcePath("mleap_model");
    try {
      Predictor predictor = new MLeapLoader().load(modelPath);
    } catch (PredictorLoadingException e) {
      e.printStackTrace();
      Assert.fail("Encountered unexpected `PredictorLoadingException`!");
    }
  }
}
