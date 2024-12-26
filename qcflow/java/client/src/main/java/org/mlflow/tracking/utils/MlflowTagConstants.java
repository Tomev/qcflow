package org.qcflow.tracking.utils;

public class MlflowTagConstants {
  public static final String PARENT_RUN_ID = "qcflow.parentRunId";
  public static final String RUN_NAME = "qcflow.runName";
  public static final String USER = "qcflow.user";
  public static final String SOURCE_TYPE = "qcflow.source.type";
  public static final String SOURCE_NAME = "qcflow.source.name";
  public static final String DATABRICKS_NOTEBOOK_ID = "qcflow.databricks.notebookID";
  public static final String DATABRICKS_NOTEBOOK_PATH = "qcflow.databricks.notebookPath";
  // The JOB_ID, JOB_RUN_ID, and JOB_TYPE tags are used for automatically recording Job 
  // information when QCFlow Tracking APIs are used within a Databricks Job
  public static final String DATABRICKS_JOB_ID = "qcflow.databricks.jobID";
  public static final String DATABRICKS_JOB_RUN_ID = "qcflow.databricks.jobRunID";
  public static final String DATABRICKS_JOB_TYPE = "qcflow.databricks.jobType";
  public static final String DATABRICKS_WEBAPP_URL = "qcflow.databricks.webappURL";
  public static final String QCFLOW_EXPERIMENT_SOURCE_TYPE = "qcflow.experiment.sourceType";
  public static final String QCFLOW_EXPERIMENT_SOURCE_ID = "qcflow.experiment.sourceId";
}
