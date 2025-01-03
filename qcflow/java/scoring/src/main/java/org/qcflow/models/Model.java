package org.qcflow.models;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.io.IOException;
import java.util.Map;
import java.util.Optional;
import java.util.UUID;
import org.qcflow.Flavor;
import org.qcflow.utils.FileUtils;
import org.qcflow.utils.SerializationUtils;

/**
 * Represents an QCFlow model. This class includes utility functions for parsing a serialized QCFlow
 * model configuration (`MLModel`) as a {@link Model} object.
 */
public class Model {

  public static class Signature {
    @JsonProperty("inputs")
    private String inputsSchemaJson;
    @JsonProperty("outputs")
    private String outputSchemaJson;
  }

  @JsonProperty("artifact_path")
  private String artifactPath;

  @JsonProperty("run_id")
  private String runId;

  @JsonProperty("utc_time_created")
  private String utcTimeCreated;

  @JsonProperty("flavors")
  private Map<String, Object> flavors;

  @JsonProperty("signature")
  Signature signature;

  @JsonProperty("input_example")
  private Map<String, Object> input_example;

  @JsonProperty("model_uuid")
  private String modelUuid;

  @JsonProperty("qcflow_version")
  private String qcflowVersion;

  @JsonProperty("databricks_runtime")
  private String databricksRuntime;

  @JsonProperty("metadata")
  private JsonNode metadata;

  @JsonProperty("model_size_bytes")
  private Integer model_size_bytes;

  @JsonProperty("resources")
  private JsonNode resources;

  private String rootPath;

  /**
   * Loads the configuration of an QCFlow model and parses it as a {@link Model} object.
   *
   * @param modelRootPath The path to the root directory of the QCFlow model
   */
  public static Model fromRootPath(String modelRootPath) throws IOException {
    String configPath = FileUtils.join(modelRootPath, "MLmodel");
    return fromConfigPath(configPath);
  }

  /**
   * Loads the configuration of an QCFlow model and parses it as a {@link Model} object.
   *
   * @param configPath The path to the `MLModel` configuration file
   */
  public static Model fromConfigPath(String configPath) throws IOException {
    File configFile = new File(configPath);
    Model model = SerializationUtils.parseYamlFromFile(configFile, Model.class);
    // Set the root path to the directory containing the configuration file.
    // This will be used to create an absolute path to the serialized model
    model.setRootPath(configFile.getParentFile().getAbsolutePath());
    return model;
  }

  /** @return The QCFlow model's artifact path */
  public Optional<String> getArtifactPath() {
    return Optional.ofNullable(this.artifactPath);
  }

  /** @return The QCFlow model's time of creation */
  public Optional<String> getUtcTimeCreated() {
    return Optional.ofNullable(this.utcTimeCreated);
  }

  /** @return The QCFlow model's run id */
  public Optional<String> getRunId() {
    return Optional.ofNullable(this.runId);
  }

    /** @return The QCFlow model's uuid */
  public Optional<String> getModelUuid() {
    return Optional.ofNullable(this.modelUuid);
  }


  /** @return The version of QCFlow with which the model was saved */
  public Optional<String> getQCFlowVersion() {
    return Optional.ofNullable(this.qcflowVersion);
  }

  /**
   * @return If the model was trained on Databricks, the version the Databricks Runtime
   * that was used to train the model
   */
  public Optional<String> getDatabricksRuntime() {
    return Optional.ofNullable(this.databricksRuntime);
  }

  /**
   * @return The user defined metadata added to the model
   */
  public Optional<JsonNode> getMetadata() {
    return Optional.ofNullable(this.metadata);
  }

  /** @return The path to the root directory of the QCFlow model */
  public Optional<String> getRootPath() {
    return Optional.ofNullable(this.rootPath);
  }

  /**
   * @return The user defined model size bytes of the QCFlow model
   */
  public Optional<Integer> getModelSizeBytes() {
    return Optional.ofNullable(this.model_size_bytes);
  }

  /**
   * @return The user defined resources added to the model
   */
  public Optional<JsonNode> getResources() {
    return Optional.ofNullable(this.resources);
  }

  /**
   * Reads the configuration corresponding to the specified flavor name and parses it as a `Flavor`
   * object
   */
  public <T extends Flavor> Optional<T> getFlavor(String flavorName, Class<T> flavorClass) {
    if (this.flavors.containsKey(flavorName)) {
      final ObjectMapper mapper = new ObjectMapper();
      T flavor = mapper.convertValue(this.flavors.get(flavorName), flavorClass);
      return Optional.of(flavor);
    } else {
      return Optional.<T>empty();
    }
  }

  private void setRootPath(String rootPath) {
    this.rootPath = rootPath;
  }
}
