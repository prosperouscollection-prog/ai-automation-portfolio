// Genesis AI Systems PWA Service Worker
const CACHE_VERSION = 'v1-2026-03-28';
const CACHE_NAME = `genesisai-cache-${CACHE_VERSION}`;
const OFFLINE_URL = '/offline.html';
const PRECACHE_URLS = [
  '/',
  '/index.html',
  '/privacy-policy.html',
  '/terms.html',
  OFFLINE_URL,
  '/manifest.json',
  '/icons/icon-192.png',
  '/icons/icon-512.png'
];

// Install: precache key static assets
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(cache => cache.addAll(PRECACHE_URLS))
      .then(() => self.skipWaiting())
  );
});

// Activate: remove old caches
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.filter(name => name !== CACHE_NAME)
          .map(name => caches.delete(name))
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch: handle requests with cache strategy + offline fallback
self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;
  const url = new URL(event.request.url);

  // HTML: network-first, fallback to cache/offline
  if (
    url.pathname.endsWith('.html') || 
    url.pathname === '/' || 
    url.pathname === ''
  ) {
    event.respondWith(
      fetch(event.request)
        .then(response => {
          const copy = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
          return response;
        })
        .catch(() => {
          return caches.match(event.request).then(res => {
            return res || caches.match(OFFLINE_URL);
          });
        })
    );
    return;
  }

  // Manifest & Icons: cache first
  if (
    url.pathname.endsWith('.json') ||
    url.pathname.endsWith('.png') ||
    url.pathname.startsWith('/icons/')
  ) {
    event.respondWith(
      caches.match(event.request)
        .then(res => {
          return res || fetch(event.request).then(response => {
            const copy = response.clone();
            caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
            return response;
          });
        })
        .catch(() => {
          if (url.pathname.endsWith('.png')) {
            return caches.match('/icons/icon-192.png');
          }
        })
    );
    return;
  }

  // Other: try network, fallback to cache/offline
  event.respondWith(
    fetch(event.request).catch(() => {
      return caches.match(event.request).then(res => {
        return res || caches.match(OFFLINE_URL);
      });
    })
  );
});

// Allow manual skipWaiting from client
self.addEventListener('message', event => {
  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }
});
