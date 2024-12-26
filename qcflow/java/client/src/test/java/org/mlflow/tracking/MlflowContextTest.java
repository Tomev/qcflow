package org.qcflow.tracking;

import static org.mockito.Mockito.*;

import static org.qcflow.api.proto.Service.*;

import org.qcflow.tracking.utils.QCFlowTagConstants;
import org.mockito.ArgumentCaptor;
import org.testng.Assert;
import org.testng.annotations.AfterMethod;
import org.testng.annotations.Test;

import java.util.List;
import java.util.Optional;

public class QCFlowContextTest {
  private static QCFlowClient mockClient;

  @AfterMethod
  public static void afterMethod() {
    mockClient = null;
  }

  public static QCFlowContext setupQCFlowContext() {
    mockClient = mock(QCFlowClient.class);
    QCFlowContext qcflow = new QCFlowContext(mockClient);
    return qcflow;
  }

  @Test
  public void testGetClient() {
    QCFlowContext qcflow = setupQCFlowContext();
    Assert.assertEquals(qcflow.getClient(), mockClient);
  }

  @Test
  public void testSetExperimentName() {
    // Will throw if there is no experiment with the same name.
    {
      QCFlowContext qcflow = setupQCFlowContext();
      when(mockClient.getExperimentByName("experiment-name")).thenReturn(Optional.empty());
      try {
        qcflow.setExperimentName("experiment-name");
        Assert.fail();
      } catch (IllegalArgumentException expected) {
      }
    }

    // Will set experiment-id if experiment is returned from getExperimentByName
    {
      QCFlowContext qcflow = setupQCFlowContext();
      when(mockClient.getExperimentByName("experiment-name")).thenReturn(
        Optional.of(Experiment.newBuilder().setExperimentId("123").build()));
      qcflow.setExperimentName("experiment-name");
      Assert.assertEquals(qcflow.getExperimentId(), "123");
    }
  }

  @Test
  public void testSetAndGetExperimentId() {
      QCFlowContext qcflow = setupQCFlowContext();
      qcflow.setExperimentId("apple");
      Assert.assertEquals(qcflow.getExperimentId(), "apple");
  }

  @Test
  public void testStartRun() {
    // Sets the appropriate tags
    ArgumentCaptor<CreateRun> createRunArgument = ArgumentCaptor.forClass(CreateRun.class);
    QCFlowContext qcflow = setupQCFlowContext();
    qcflow.setExperimentId("123");
    qcflow.startRun("apple", "parent-run-id");
    verify(mockClient).createRun(createRunArgument.capture());
    List<RunTag> tags = createRunArgument.getValue().getTagsList();
    Assert.assertEquals(createRunArgument.getValue().getExperimentId(), "123");
    Assert.assertTrue(tags.contains(createRunTag(QCFlowTagConstants.RUN_NAME, "apple")));
    Assert.assertTrue(tags.contains(createRunTag(QCFlowTagConstants.SOURCE_TYPE, "LOCAL")));
    Assert.assertTrue(tags.contains(createRunTag(QCFlowTagConstants.USER, System.getProperty("user.name"))));
    Assert.assertTrue(tags.contains(createRunTag(QCFlowTagConstants.PARENT_RUN_ID, "parent-run-id")));
  }

  @Test
  public void testStartRunWithNoRunName() {
    // Sets the appropriate tags
    ArgumentCaptor<CreateRun> createRunArgument = ArgumentCaptor.forClass(CreateRun.class);
    QCFlowContext qcflow = setupQCFlowContext();
    qcflow.startRun();
    verify(mockClient).createRun(createRunArgument.capture());
    List<RunTag> tags = createRunArgument.getValue().getTagsList();
    Assert.assertFalse(
      tags.stream().anyMatch(tag -> tag.getKey().equals(QCFlowTagConstants.RUN_NAME)));
  }

  @Test
  public void testWithActiveRun() {
    // Sets the appropriate tags
    QCFlowContext qcflow = setupQCFlowContext();
    qcflow.setExperimentId("123");
    when(mockClient.createRun(any(CreateRun.class)))
      .thenReturn(RunInfo.newBuilder().setRunId("test-id").build());
    qcflow.withActiveRun("apple", activeRun -> {
      Assert.assertEquals(activeRun.getId(), "test-id");
    });
    verify(mockClient).createRun(any(CreateRun.class));
    verify(mockClient).setTerminated(any(), any());
  }

  @Test
  public void testWithActiveRunNoRunName() {
    // Sets the appropriate tags
    QCFlowContext qcflow = setupQCFlowContext();
    qcflow.setExperimentId("123");
    when(mockClient.createRun(any(CreateRun.class)))
      .thenReturn(RunInfo.newBuilder().setRunId("test-id").build());
    qcflow.withActiveRun(activeRun -> {
      Assert.assertEquals(activeRun.getId(), "test-id");
    });
    verify(mockClient).createRun(any(CreateRun.class));
    verify(mockClient).setTerminated(any(), any());
  }


  private static RunTag createRunTag(String key, String value) {
    return RunTag.newBuilder().setKey(key).setValue(value).build();
  }
}