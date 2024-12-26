package org.qcflow.tracking.samples;

import com.google.common.collect.ImmutableMap;
import org.qcflow.tracking.ActiveRun;
import org.qcflow.tracking.MlflowContext;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;

public class FluentExample {
  public static void main(String[] args) {
    MlflowContext qcflow = new MlflowContext();
    ExecutorService executor = Executors.newFixedThreadPool(10);

    // Vanilla usage
    {
      ActiveRun run = qcflow.startRun("run");
      run.logParam("alpha", "0.0");
      run.logMetric("MSE", 0.0);
      run.setTags(ImmutableMap.of(
        "company", "databricks",
        "org", "engineering"
      ));
      run.endRun();
    }

    // Lambda usage
    {
      qcflow.withActiveRun("lambda run", (activeRun -> {
        activeRun.logParam("layers", "4");
        // Perform training code
      }));
    }
    // Log one parent run and 5 children run
    {
      ActiveRun run = qcflow.startRun("parent run");
      for (int i = 0; i <= 5; i++) {
        ActiveRun childRun = qcflow.startRun("child run", run.getId());
        childRun.logParam("iteration", Integer.toString(i));
        childRun.endRun();
      }
      run.endRun();
    }

    // Log one parent run and 5 children run (multithreaded)
    {
      ActiveRun run = qcflow.startRun("parent run (multithreaded)");
      for (int i = 0; i <= 5; i++) {
        final int i0 = i;
        executor.submit(() -> {
          ActiveRun childRun = qcflow.startRun("child run (multithreaded)", run.getId());
          childRun.logParam("iteration", Integer.toString(i0));
          childRun.endRun();
        });
      }
      run.endRun();
    }
    executor.shutdown();
    qcflow.getClient().close();
  }
}
