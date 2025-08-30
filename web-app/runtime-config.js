/**
 * Runtime configuration for front-end (public, no secrets).
 * - In local dev (served by Node on http://localhost:3001), keep empty base so fetch('/api/...') hits the same origin.
 * - In production (Cloudflare Pages), set these to your Railway service URLs.
 */
(function () {
  var isLocal =
    location.hostname === 'localhost' ||
    location.hostname === '127.0.0.1';

  // TODO: After deploying backends on Railway, replace the placeholders below.
  window.RUNTIME_CONFIG = {
    // If left empty, front-end will call same-origin '/api/...'
    NODE_API_BASE: isLocal ? '' : 'https://YOUR-NODE-SERVICE.up.railway.app',
    // Only needed if the web-app calls Python endpoints directly from the browser
    PY_API_BASE: isLocal ? '' : 'https://YOUR-PYTHON-SERVICE.up.railway.app'
  };
})();
