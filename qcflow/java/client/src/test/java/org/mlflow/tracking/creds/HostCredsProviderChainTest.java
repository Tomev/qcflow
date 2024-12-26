package org.qcflow.tracking.creds;

import org.testng.Assert;
import org.testng.annotations.BeforeMethod;
import org.testng.annotations.Test;

import org.qcflow.tracking.QCFlowClientException;

public class HostCredsProviderChainTest {
  private boolean refreshCalled = false;
  private boolean throwException = false;
  private QCFlowHostCreds providedHostCreds = null;
  private QCFlowHostCredsProvider myHostCredsProvider = new MyHostCredsProvider();

  class MyHostCredsProvider implements QCFlowHostCredsProvider {
    @Override
    public QCFlowHostCreds getHostCreds() {
      if (throwException) {
        throw new IllegalStateException("Oh no!");
      }
      return providedHostCreds;
    }

    @Override
    public void refresh() {
      refreshCalled = true;
    }
  }

  @BeforeMethod
  public void beforeEach() {
    refreshCalled = false;
    throwException = false;
    providedHostCreds = null;
  }

  @Test
  public void testUseFirstIfAvailable() {
    BasicQCFlowHostCreds secondCreds = new BasicQCFlowHostCreds("hosty", "tokeny");
    HostCredsProviderChain chain = new HostCredsProviderChain(myHostCredsProvider, secondCreds);

    // If we have valid credentials, we should be used.
    providedHostCreds = new BasicQCFlowHostCreds("new-host");
    Assert.assertEquals(chain.getHostCreds().getHost(), "new-host");
    Assert.assertNull(chain.getHostCreds().getToken());

    // If our credentials are invalid, we should be skipped.
    providedHostCreds = new BasicQCFlowHostCreds(null);
    Assert.assertEquals(chain.getHostCreds().getHost(), "hosty");
    Assert.assertEquals(chain.getHostCreds().getToken(), "tokeny");

    // If we return null, we should be skipped.
    providedHostCreds = null;
    Assert.assertEquals(chain.getHostCreds().getHost(), "hosty");
    Assert.assertEquals(chain.getHostCreds().getToken(), "tokeny");

    // If we return an exception, we should be skipped.
    throwException = true;
    Assert.assertEquals(chain.getHostCreds().getHost(), "hosty");
    Assert.assertEquals(chain.getHostCreds().getToken(), "tokeny");
  }

  @Test
  public void testRefreshPropagates() {
    HostCredsProviderChain chain = new HostCredsProviderChain(myHostCredsProvider);
    Assert.assertFalse(refreshCalled);
    chain.refresh();
    Assert.assertTrue(refreshCalled);
  }

  @Test
  public void testThrowFinalError() {
    throwException = true;
    HostCredsProviderChain chain = new HostCredsProviderChain(myHostCredsProvider);
    try {
      chain.getHostCreds().getHost();
    } catch (QCFlowClientException e) {
      Assert.assertTrue(e.getMessage().contains("Oh no!"), e.getMessage());
    }
  }
}
