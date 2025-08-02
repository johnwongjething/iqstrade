const { createProxyMiddleware } = require('http-proxy-middleware');

module.exports = function(app) {
  // Proxy API calls to backend during development
  app.use(
    '/api',
    createProxyMiddleware({
      target: 'http://localhost:5000', // Backend URL
      changeOrigin: true,
      secure: false,
      // Preserve cookies for CSRF
      cookieDomainRewrite: {
        '*': 'localhost'
      },
      // Log proxy requests in development
      logLevel: 'debug',
      onProxyReq: (proxyReq, req, res) => {
        // Log the proxy request
        console.log(`🔗 Proxying: ${req.method} ${req.url} -> ${proxyReq.path}`);
      },
      onProxyRes: (proxyRes, req, res) => {
        // Log the proxy response
        console.log(`✅ Proxied: ${req.method} ${req.url} -> ${proxyRes.statusCode}`);
      }
    })
  );

  // Proxy other backend routes
  app.use(
    ['/firebase-messaging-sw.js', '/manifest.json', '/logo192.png', '/whatsapp-icon.png'],
    createProxyMiddleware({
      target: 'http://localhost:5000',
      changeOrigin: true,
      secure: false
    })
  );
}; 