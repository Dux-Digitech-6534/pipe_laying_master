const CACHE_NAME = "cmr-pwa-shell-v1";
const STATIC_PATH_HINTS = ["/assets/cmr_pipe_laying_master/"];

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((names) =>
      Promise.all(names.filter((name) => name !== CACHE_NAME).map((name) => caches.delete(name)))
    )
  );
  self.clients.claim();
});

// Only cache this app's own static bundle/icons (JS, CSS, images). Every other
// request (API calls, HTML, other apps on this bench) always goes to the network,
// since caching live business data would show stale stock/records instead of real ones.
self.addEventListener("fetch", (event) => {
  const url = new URL(event.request.url);
  const isOwnStaticAsset = STATIC_PATH_HINTS.some((hint) => url.pathname.startsWith(hint));
  if (event.request.method !== "GET" || !isOwnStaticAsset) return;

  event.respondWith(
    caches.open(CACHE_NAME).then((cache) =>
      cache.match(event.request).then((cached) => {
        const network = fetch(event.request)
          .then((response) => {
            if (response.ok) cache.put(event.request, response.clone());
            return response;
          })
          .catch(() => cached);
        return cached || network;
      })
    )
  );
});
