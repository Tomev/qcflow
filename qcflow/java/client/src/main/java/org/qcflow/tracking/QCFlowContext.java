package org.qcflow.tracking;

import org.qcflow.api.proto.Service.*;
import org.qcflow.tracking.utils.DatabricksContext;
import org.qcflow.tracking.utils.QCFlowTagConstants;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import java.util.*;
import java.util.function.Consumer;

/**
 * Main entrypoint used to start QCFlow runs to log to. This is a higher level interface than
 * {@code QCFlowClient} and provides convenience methods to keep track of active runs and to set
 * default tags on runs which are created through {@code QCFlowContext}
 *
 * On construction, QCFlowContext will choose a default experiment ID to log to depending on your
 * environment. To log to a different experiment, use {@link #setExperimentId(String)} or
 * {@link #setExperimentName(String)}
 *
 * <p>
 * For example:
 *   <pre>
 *   // Uses the URI set in the QCFLOW_TRACKING_URI environment variable.
 *   // To use your own tracking uri set it in the call to "new QCFlowContext("tracking-uri")"
 *   QCFlowContext qcflow = new QCFlowContext();
 *   ActiveRun run = qcflow.startRun("run-name");
 *   run.logParam("alpha", "0.5");
 *   run.logMetric("MSE", 0.0);
 *   run.endRun();
 *   </pre>
 */
public class QCFlowContext {
  private QCFlowClient client;
  private String experimentId;
  // Cache the default experiment ID for a repo notebook to avoid sending
  // extraneous API requests
  private static String defaultRepoNotebookExperimentId;
  private static final Logger logger = LoggerFactory.getLogger(QCFlowContext.class);


  /**
   * Constructs a {@code QCFlowContext} with a QCFlowClient based on the QCFLOW_TRACKING_URI
   * environment variable.
   */
  public QCFlowContext() {
    this(new QCFlowClient());
  }

  /**
   * Constructs a {@code QCFlowContext} which points to the specified trackingUri.
   *
   * @param trackingUri The URI to log to.
   */
  public QCFlowContext(String trackingUri) {
    this(new QCFlowClient(trackingUri));
  }

  /**
   * Constructs a {@code QCFlowContext} which points to the specified trackingUri.
   *
   * @param client The client used to log runs.
   */
  public QCFlowContext(QCFlowClient client) {
    this.client = client;
    this.experimentId = getDefaultExperimentId();
  }

  /**
   * Returns the client used to log runs.
   *
   * @return the client used to log runs.
   */
  public QCFlowClient getClient() {
    return this.client;
  }

  /**
   * Sets the experiment to log runs to by name.
   * @param experimentName the name of the experiment to log runs to.
   * @throws IllegalArgumentException if the experiment name does not match an existing experiment
   */
  public QCFlowContext setExperimentName(String experimentName) throws IllegalArgumentException {
    Optional<Experiment> experimentOpt = client.getExperimentByName(experimentName);
    if (!experimentOpt.isPresent()) {
      throw new IllegalArgumentException(
        String.format("%s is not a valid experiment", experimentName));
    }
    experimentId = experimentOpt.get().getExperimentId();
    return this;
  }

  /**
   * Sets the experiment to log runs to by ID.
   * @param experimentId the id of the experiment to log runs to.
   */
  public QCFlowContext setExperimentId(String experimentId) {
    this.experimentId = experimentId;
    return this;
  }

  /**
   * Returns the experiment ID we are logging to.
   *
   * @return the experiment ID we are logging to.
   */
  public String getExperimentId() {
    return this.experimentId;
  }

  /**
   * Starts a QCFlow run without a name. To log data to newly created QCFlow run see the methods on
   * {@link ActiveRun}. QCFlow runs should be ended using {@link ActiveRun#endRun()}
   *
   * @return An {@code ActiveRun} object to log data to.
   */
  public ActiveRun startRun() {
    return startRun(null);
  }

  /**
   * Starts a QCFlow run. To log data to newly created QCFlow run see the methods on
   * {@link ActiveRun}. QCFlow runs should be ended using {@link ActiveRun#endRun()}
   *
   * @param runName The name of this run. For display purposes only and is stored in the
   *                qcflow.runName tag.
   * @return An {@code ActiveRun} object to log data to.
   */
  public ActiveRun startRun(String runName) {
    return startRun(runName, null);
  }

  /**
   * Like {@link #startRun(String)} but sets the {@code qcflow.parentRunId} tag in order to create
   * nested runs.
   *
   * @param runName The name of this run. For display purposes only and is stored in the
   *                qcflow.runName tag.
   * @param parentRunId The ID of this run's parent
   * @return An {@code ActiveRun} object to log data to.
   */
  public ActiveRun startRun(String runName, String parentRunId) {
    Map<String, String> tags = new HashMap<>();
    if (runName != null) {
      tags.put(QCFlowTagConstants.RUN_NAME, runName);
    }
    tags.put(QCFlowTagConstants.USER, System.getProperty("user.name"));
    tags.put(QCFlowTagConstants.SOURCE_TYPE, "LOCAL");
    if (parentRunId != null) {
      tags.put(QCFlowTagConstants.PARENT_RUN_ID, parentRunId);
    }

    // Add tags from DatabricksContext if they exist
    DatabricksContext databricksContext = DatabricksContext.createIfAvailable();
    if (databricksContext != null) {
      tags.putAll(databricksContext.getTags());
    }

    CreateRun.Builder createRunBuilder = CreateRun.newBuilder()
      .setExperimentId(experimentId)
      .setStartTime(System.currentTimeMillis());
    for (Map.Entry<String, String> tag: tags.entrySet()) {
      createRunBuilder.addTags(
        RunTag.newBuilder().setKey(tag.getKey()).setValue(tag.getValue()).build());
    }
    RunInfo runInfo = client.createRun(createRunBuilder.build());

    ActiveRun newRun = new ActiveRun(runInfo, client);
    return newRun;
  }

  /**
   * Like {@link #startRun(String)} but will terminate the run after the activeRunFunction is
   * executed.
   *
   * For example
   *   <pre>
   *   qcflowContext.withActiveRun((activeRun -&gt; {
   *     activeRun.logParam("layers", "4");
   *   }));
   *   </pre>
   *
   * @param activeRunFunction A function which takes an {@code ActiveRun} and logs data to it.
   */
  public void withActiveRun(Consumer<ActiveRun> activeRunFunction) {
    ActiveRun newRun = startRun();
    try {
      activeRunFunction.accept(newRun);
    } catch(Exception e) {
      newRun.endRun(RunStatus.FAILED);
      return;
    }
    newRun.endRun(RunStatus.FINISHED);
  }

  /**
   * Like {@link #withActiveRun(Consumer)} with an explicity run name.
   *
   * @param runName The name of this run. For display purposes only and is stored in the
   *                qcflow.runName tag.
   * @param activeRunFunction A function which takes an {@code ActiveRun} and logs data to it.
   */
  public void withActiveRun(String runName, Consumer<ActiveRun> activeRunFunction) {
    ActiveRun newRun = startRun(runName);
    try {
      activeRunFunction.accept(newRun);
    } catch(Exception e) {
      newRun.endRun(RunStatus.FAILED);
      return;
    }
    newRun.endRun(RunStatus.FINISHED);
  }

  private static String getDefaultRepoNotebookExperimentId(String notebookId, String notebookPath) {
      if (defaultRepoNotebookExperimentId != null) {
        return defaultRepoNotebookExperimentId;
      }
      CreateExperiment.Builder request = CreateExperiment.newBuilder();
      request.setName(notebookPath);
      request.addTags(ExperimentTag.newBuilder()
              .setKey(QCFlowTagConstants.QCFLOW_EXPERIMENT_SOURCE_TYPE)
              .setValue("REPO_NOTEBOOK")
      );
      request.addTags(ExperimentTag.newBuilder()
              .setKey(QCFlowTagConstants.QCFLOW_EXPERIMENT_SOURCE_ID)
              .setValue(notebookId)
      );
      String experimentId = (new QCFlowClient()).createExperiment(request.build());
      defaultRepoNotebookExperimentId = experimentId;
      return experimentId;

  }

  private static String getDefaultExperimentId() {
    DatabricksContext databricksContext = DatabricksContext.createIfAvailable();
    if (databricksContext != null && databricksContext.isInDatabricksNotebook()) {
      String notebookId = databricksContext.getNotebookId();
      String notebookPath = databricksContext.getNotebookPath();
      if (notebookId != null) {
        if (notebookPath != null && notebookPath.startsWith("/Repos")) {
          try {
            return getDefaultRepoNotebookExperimentId(notebookId, notebookPath);
          }
          catch (Exception e) {
            // Do nothing; will fall through to returning notebookId
            logger.warn("Failed to get default repo notebook experiment ID", e);
          }
        }
        return notebookId;
      }
    }
    return QCFlowClient.DEFAULT_EXPERIMENT_ID;
  }
}
