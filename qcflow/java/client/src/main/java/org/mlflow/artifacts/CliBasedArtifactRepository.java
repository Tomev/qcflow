package org.qcflow.artifacts;

import java.io.File;
import java.io.IOException;
import java.lang.reflect.Type;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.atomic.AtomicBoolean;

import com.google.common.annotations.VisibleForTesting;
import com.google.common.collect.Lists;
import com.google.gson.Gson;
import com.google.gson.reflect.TypeToken;
import com.google.protobuf.InvalidProtocolBufferException;
import com.google.protobuf.util.JsonFormat;
import org.apache.commons.io.IOUtils;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;

import org.qcflow.api.proto.Service;
import org.qcflow.tracking.QCFlowClientException;
import org.qcflow.tracking.creds.QCFlowHostCreds;
import org.qcflow.tracking.creds.DatabricksQCFlowHostCreds;
import org.qcflow.tracking.creds.QCFlowHostCredsProvider;

/**
 * Shells out to the 'qcflow' command line utility to upload, download, and list artifacts. This
 * is used as a fallback to implement any artifact repositories which are not natively supported
 * within Java.
 *
 * We require that 'qcflow' is available in the system path.
 */
public class CliBasedArtifactRepository implements ArtifactRepository {
  private static final Logger logger = LoggerFactory.getLogger(CliBasedArtifactRepository.class);

  // Global check if we ever successfully loaded 'qcflow'. This allows us to print a more
  // helpful error message if the executable is not in the path.
  private static final AtomicBoolean qcflowSuccessfullyLoaded = new AtomicBoolean(false);

  // Name of the Python CLI utility which can be exec'd directly, with QCFlow on its path
  private final String PYTHON_EXECUTABLE =
    Optional.ofNullable(System.getenv("QCFLOW_PYTHON_EXECUTABLE")).orElse("python");

  // Python CLI command
  private final String PYTHON_COMMAND = "qcflow.store.artifact.cli";

  // Base directory of the artifactory, used to let the user know why this repository was chosen.
  private final String artifactBaseDir;

  // Run ID this repository is targeting.
  private final String runId;

  // Used to pass credentials as environment variables
  // (e.g., QCFLOW_TRACKING_URI or DATABRICKS_HOST) to the qcflow process.
  private final QCFlowHostCredsProvider hostCredsProvider;

  public CliBasedArtifactRepository(
      String artifactBaseDir,
      String runId,
      QCFlowHostCredsProvider hostCredsProvider) {
    this.artifactBaseDir = artifactBaseDir;
    this.runId = runId;
    this.hostCredsProvider = hostCredsProvider;
  }

  @Override
  public void logArtifact(File localFile, String artifactPath) {
    checkQCFlowAccessible();
    if (!localFile.exists()) {
      throw new QCFlowClientException("Local file does not exist: " + localFile);
    }
    if (localFile.isDirectory()) {
      throw new QCFlowClientException("Local path points to a directory. Use logArtifacts" +
        " instead: " + localFile);
    }

    List<String> baseCommand = Lists.newArrayList(
      "log-artifact", "--local-file", localFile.toString());
    List<String> command = appendRunIdArtifactPath(baseCommand, runId, artifactPath);
    String tag = "log file " + localFile + " to " + getTargetIdentifier(artifactPath);
    forkQCFlowProcess(command, tag);
  }

  @Override
  public void logArtifact(File localFile) {
    logArtifact(localFile, null);
  }

  @Override
  public void logArtifacts(File localDir, String artifactPath) {
    checkQCFlowAccessible();
    if (!localDir.exists()) {
      throw new QCFlowClientException("Local file does not exist: " + localDir);
    }
    if (localDir.isFile()) {
      throw new QCFlowClientException("Local path points to a file. Use logArtifact" +
        " instead: " + localDir);
    }

    List<String> baseCommand = Lists.newArrayList(
      "log-artifacts", "--local-dir", localDir.toString());
    List<String> command = appendRunIdArtifactPath(baseCommand, runId, artifactPath);
    String tag = "log dir " + localDir + " to " + getTargetIdentifier(artifactPath);
    forkQCFlowProcess(command, tag);
  }

  @Override
  public void logArtifacts(File localDir) {
    logArtifacts(localDir, null);
  }

  @Override
  public File downloadArtifacts(String artifactPath) {
    checkQCFlowAccessible();
    String tag = "download artifacts for " + getTargetIdentifier(artifactPath);
    List<String> command = appendRunIdArtifactPath(
      Lists.newArrayList("download"), runId, artifactPath);
    String stdOutput = forkQCFlowProcess(command, tag);
    String[] splits = stdOutput.split(System.lineSeparator());
    return new File(splits[splits.length-1].trim());
  }

  @Override
  public File downloadArtifacts() {
    return downloadArtifacts(null);
  }

  @Override
  public List<Service.FileInfo> listArtifacts(String artifactPath) {
    checkQCFlowAccessible();
    String tag = "list artifacts in " + getTargetIdentifier(artifactPath);
    List<String> command = appendRunIdArtifactPath(
      Lists.newArrayList("list"), runId, artifactPath);
    String jsonOutput = forkQCFlowProcess(command, tag);
    return parseFileInfos(jsonOutput);
  }

  @Override
  public List<Service.FileInfo> listArtifacts() {
    return listArtifacts(null);
  }

  /**
   * Only available in the CliBasedArtifactRepository. Downloads an artifact to the local
   * filesystem when provided with an artifact uri. This method should not be used directly
   * by the user. Please use {@link org.qcflow.tracking.QCFlowClient}
   *
   * @param artifactUri Artifact uri
   * @return Directory/file of the artifact
   */
  public File downloadArtifactFromUri(String artifactUri) {
    checkQCFlowAccessible();
    String tag = "download artifacts for " + artifactUri;
    List<String> command = Lists.newArrayList("download", "--artifact-uri", artifactUri);
    String localPath = forkQCFlowProcess(command, tag).trim();
    return new File(localPath);
  }

  /** Parses a list of JSON FileInfos, as returned by 'qcflow artifacts list'. */
  private List<Service.FileInfo> parseFileInfos(String json) {
    // The protobuf deserializer doesn't allow us to directly deserialize a list, so we
    // deserialize a list-of-dictionaries, and then reserialize each dictionary to pass it to
    // the protobuf deserializer.
    Gson gson = new Gson();
    Type type = new TypeToken<List<Map<String, Object>>>(){}.getType();
    List<Map<String, Object>> listOfDicts = gson.fromJson(json, type);
    List<Service.FileInfo> fileInfos = new ArrayList<>();
    for (Map<String, Object> dict: listOfDicts) {
      String fileInfoJson = gson.toJson(dict);
      try {
        Service.FileInfo.Builder builder = Service.FileInfo.newBuilder();
        JsonFormat.parser().merge(fileInfoJson, builder);
        fileInfos.add(builder.build());
      } catch (InvalidProtocolBufferException e) {
        throw new QCFlowClientException("Failed to deserialize JSON into FileInfo: " + json, e);
      }
    }
    return fileInfos;
  }

  /**
   * Checks whether the 'qcflow' executable is available, and throws a nice error if not.
   * If this method has ever run successfully before (in the entire JVM), we will not rerun it.
   */
  private void checkQCFlowAccessible() {
    if (qcflowSuccessfullyLoaded.get()) {
      return;
    }

    try {
      String tag = "get qcflow version";
      forkQCFlowProcess(Lists.newArrayList("--help"), tag);
      logger.info("Found local qcflow executable");
      qcflowSuccessfullyLoaded.set(true);
    } catch (QCFlowClientException e) {
      String errorMessage = String.format("Failed to exec '%s -m %s', needed to" +
          " access artifacts within the non-Java-native artifact store at '%s'. Please make" +
          " sure qcflow is available on your local system path (e.g., from 'pip install qcflow')",
        PYTHON_EXECUTABLE, PYTHON_COMMAND, artifactBaseDir);
      throw new QCFlowClientException(errorMessage, e);
    }
  }

  /**
   * Forks the given qcflow command and awaits for its successful completion.
   *
   * @param qcflowCommand List of arguments to invoke qcflow with.
   * @param tag User-facing tag which will be used to identify what we were trying to do
   *            in the case of a failure.
   * @return raw stdout of the process, decoded as a utf-8 string
   * @throws QCFlowClientException if the process exits with a non-zero exit code, or anything
   *                               else goes wrong.
   */
  private String forkQCFlowProcess(List<String> qcflowCommand, String tag) {
    String stdout;
    Process process = null;
    try {
      QCFlowHostCreds hostCreds = hostCredsProvider.getHostCreds();
      List<String> fullCommand = Lists.newArrayList(PYTHON_EXECUTABLE, "-m", PYTHON_COMMAND);
      fullCommand.addAll(qcflowCommand);
      ProcessBuilder pb = new ProcessBuilder(fullCommand);
      if (hostCreds instanceof DatabricksQCFlowHostCreds) {
        setProcessEnvironmentDatabricks(pb.environment(), (DatabricksQCFlowHostCreds) hostCreds);
      } else {
        setProcessEnvironment(pb.environment(), hostCreds);
      }
      process = pb.start();
      stdout = IOUtils.toString(process.getInputStream(), StandardCharsets.UTF_8);
      int exitValue = process.waitFor();
      if (exitValue != 0) {
        throw new QCFlowClientException("Failed to " + tag + ". Error: " +
          getErrorBestEffort(process));
      }
    } catch (IOException | InterruptedException e) {
      throw new QCFlowClientException("Failed to fork qcflow process to " + tag +
        ". Process stderr: " + getErrorBestEffort(process), e);
    }
    return stdout;
  }

  @VisibleForTesting
  void setProcessEnvironment(Map<String, String> environment, QCFlowHostCreds hostCreds) {
    environment.put("QCFLOW_TRACKING_URI", hostCreds.getHost());
    if (hostCreds.getUsername() != null) {
      environment.put("QCFLOW_TRACKING_USERNAME", hostCreds.getUsername());
    }
    if (hostCreds.getPassword() != null) {
      environment.put("QCFLOW_TRACKING_PASSWORD", hostCreds.getPassword());
    }
    if (hostCreds.getToken() != null) {
      environment.put("QCFLOW_TRACKING_TOKEN", hostCreds.getToken());
    }
    if (hostCreds.shouldIgnoreTlsVerification()) {
      environment.put("QCFLOW_TRACKING_INSECURE_TLS", "true");
    }
  }

  @VisibleForTesting
  void setProcessEnvironmentDatabricks(
      Map<String, String> environment,
      DatabricksQCFlowHostCreds hostCreds) {
    environment.put("DATABRICKS_HOST", hostCreds.getHost());
    if (hostCreds.getUsername() != null) {
      environment.put("DATABRICKS_USERNAME", hostCreds.getUsername());
    }
    if (hostCreds.getPassword() != null) {
      environment.put("DATABRICKS_PASSWORD", hostCreds.getPassword());
    }
    if (hostCreds.getToken() != null) {
      environment.put("DATABRICKS_TOKEN", hostCreds.getToken());
    }
    if (hostCreds.shouldIgnoreTlsVerification()) {
      environment.put("DATABRICKS_INSECURE", "true");
    }
  }

  /** Does our best to get the process's stderr, or returns a dummy return value. */
  private String getErrorBestEffort(Process process) {
    if (process == null) {
      return "<process not started>";
    }
    try {
      return IOUtils.toString(process.getErrorStream(), StandardCharsets.UTF_8);
    } catch (IOException e) {
      return "<error unknown>";
    }
  }

  /** Appends --run-id $runId and --artifact-path $artifactPath, omitting artifactPath if null. */
  private List<String> appendRunIdArtifactPath(
      List<String> baseCommand,
      String runId,
      String artifactPath) {
    baseCommand.add("--run-id");
    baseCommand.add(runId);
    if (artifactPath != null) {
      baseCommand.add("--artifact-path");
      baseCommand.add(artifactPath);
    }
    return baseCommand;
  }

  /** Returns user-facing identifier "runId=abc, artifactId=/foo", omitting artifactPath if null. */
  private String getTargetIdentifier(String artifactPath) {
    String identifier = "runId=" + runId;
    if (artifactPath != null) {
      return identifier + ", artifactPath=" + artifactPath;
    }
    return identifier;
  }
}
