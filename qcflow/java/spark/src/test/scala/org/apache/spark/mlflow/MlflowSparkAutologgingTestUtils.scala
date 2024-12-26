package org.apache.spark.qcflow

import org.apache.spark.scheduler.SparkListenerInterface
import org.apache.spark.sql.SparkSession
import org.qcflow.spark.autologging.SparkDataSourceListener

/** Test-only object used to access Spark-private fields */
object MlflowSparkAutologgingTestUtils {
  def getListeners(spark: SparkSession): Seq[SparkListenerInterface] = {
    spark.sparkContext.listenerBus.findListenersByClass[SparkDataSourceListener]
  }
}
