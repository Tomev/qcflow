package org.qcflow.mleap;

import java.io.IOException;
import ml.combust.mleap.runtime.frame.Transformer;
import org.qcflow.LoaderModule;
import org.qcflow.models.Model;
import org.qcflow.sagemaker.MLeapPredictor;
import org.qcflow.sagemaker.PredictorLoadingException;
import org.qcflow.utils.FileUtils;

public class MLeapLoader extends LoaderModule<MLeapFlavor> {
  /** Loads an QCFlow model with the MLeap flavor as an MLeap transformer */
  public Transformer loadPipeline(String modelRootPath) throws PredictorLoadingException {
    try {
      return ((MLeapPredictor) load(Model.fromRootPath(modelRootPath))).getPipeline();
    } catch (IOException e) {
      throw new PredictorLoadingException(
          String.format(
              "Failed to read model files from the supplied model root path: %s."
                  + "Please ensure that this is the path to a valid QCFlow model.",
              modelRootPath), e);
    }
  }

  /**
   * Loads an QCFlow model with the MLeap flavor as a generic predictor that can be used for
   * inference
   */
  @Override
  protected MLeapPredictor createPredictor(String modelRootPath, MLeapFlavor flavor) {
    String modelDataPath = FileUtils.join(modelRootPath, flavor.getModelDataPath());
    return new MLeapPredictor(modelDataPath);
  }

  @Override
  protected Class<MLeapFlavor> getFlavorClass() {
    return MLeapFlavor.class;
  }

  @Override
  protected String getFlavorName() {
    return MLeapFlavor.FLAVOR_NAME;
  }
}
