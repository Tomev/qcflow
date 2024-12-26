const { createProxyMiddleware } = require('http-proxy-middleware');

// eslint-disable-next-line
module.exports = function (app) {
  // The QCFlow Gunicorn server is running on port 5000, so we should redirect server requests
  // (eg /ajax-api) to that port.
  // Exception: If the caller has specified an QCFLOW_PROXY, we instead forward server requests
  // there.
  // eslint-disable-next-line no-undef
  const proxyTarget = process.env.QCFLOW_PROXY || 'http://localhost:5000/';
  // eslint-disable-next-line no-undef
  const proxyStaticTarget = process.env.QCFLOW_STATIC_PROXY || proxyTarget;
  app.use(
    createProxyMiddleware('/ajax-api', {
      target: proxyTarget,
      changeOrigin: true,
    }),
  );
  app.use(
    createProxyMiddleware('/graphql', {
      target: proxyTarget,
      changeOrigin: true,
    }),
  );
  app.use(
    createProxyMiddleware('/get-artifact', {
      target: proxyStaticTarget,
      ws: true,
      changeOrigin: true,
    }),
  );
  app.use(
    createProxyMiddleware('/model-versions/get-artifact', {
      target: proxyStaticTarget,
      ws: true,
      changeOrigin: true,
    }),
  );
};
