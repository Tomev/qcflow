package org.qcflow;

import java.io.IOException;
import java.util.Optional;
import org.qcflow.models.Model;
import org.qcflow.sagemaker.Predictor;
import org.qcflow.sagemaker.PredictorLoadingException;

/**
 * A generic loader for encapsulating flavor-specific model deserialization logic. By extending
 * {@link LoaderModule}, models of a specific flavor can be loaded as generic {@link Predictor}
 * objects. This allows tools, such as model containers, to use the models for inference
 */
public abstract class LoaderModule<T extends Flavor> {
  /**
   * Loads an QCFlow model as a generic predictor that can be used for inference
   *
   * Throws {@link PredictorLoadingException} for any failure encountered while attempting to load
   *     the model
   */
  public Predictor load(Model model) {
    Optional<T> flavor = model.getFlavor(getFlavorName(), getFlavorClass());
    if (!flavor.isPresent()) {
      throw new PredictorLoadingException(
          String.format(
              "Attempted to load the %s flavor of the model,"
                  + " but the model does not have this flavor.",
              getFlavorName()));
    }
    Optional<String> rootPath = model.getRootPath();
    if (!rootPath.isPresent()) {
      throw new PredictorLoadingException(
          "An internal error occurred while loading the model:"
              + " the model's root path could not be found. Please ensure that this"
              + " model was created using `Model.fromRootPath()` or `Model.fromConfigPath()`");
    }
    return createPredictor(rootPath.get(), flavor.get());
  }

  /**
   * Loads an QCFlow model as a generic predictor that can be used for inference
   * Throws {@link PredictorLoadingException} for any failure encountered while attempting to load
   *     the model
   *
   * @param modelRootPath The path to the root directory of the QCFlow model
   */
  public Predictor load(String modelRootPath) throws PredictorLoadingException {
    try {
      Optional<Model> model = Optional.of(Model.fromRootPath(modelRootPath));
      return load(model.get());
    } catch (IOException e) {
      throw new PredictorLoadingException(
          "Failed to load the model configuration at the specified path. Please ensure that"
              + " this is the path to the root directory of a valid QCFlow model", e);
    }
  }

  /**
   * Creates a {@link Predictor} from an QCFlow model using the specified flavor configuration
   *
   * <p>Implementations of this method are expected to throw a {@link PredictorLoadingException}
   * when errors are encountered while loading the model
   *
   * @param modelRootPath The path to the root directory of the QCFlow model
   * @param flavor The flavor configuration to use when creating the {@link Predictor}. This
   *     configuration provides additional metadata that may be necessary for {@link Predictor}
   *     creation.
   */
  protected abstract Predictor createPredictor(String modelRootPath, T flavor)
      throws PredictorLoadingException;

  /**
   * @return The {@link org.qcflow.Flavor} class associated with this loader module. This is
   *     required during the {@link #load(Model)} procedure
   */
  protected abstract Class<T> getFlavorClass();

  /**
   * @return The name of the flavor associated with this loader module. module. This is required
   *     during the {@link #load(Model)} procedure
   */
  protected abstract String getFlavorName();
}
