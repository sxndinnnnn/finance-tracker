// Minimal service worker — satisfies PWA installability criteria.
// No offline caching yet; every request just passes through to the network.
self.addEventListener("install", () => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(self.clients.claim());
});

self.addEventListener("fetch", () => {
  // Intentionally a no-op — let the browser handle the request normally.
});
