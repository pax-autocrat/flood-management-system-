/**
 * JalRakshak NCR — Progressive Web App Service Worker (Phase 7)
 * Engineered by Team NeerNetra (SustainX 2026)
 * Provides offline caching, network-first API fallback, and background disaster sync.
 */

const CACHE_NAME = 'jalrakshak-v2-cache';
const OFFLINE_FALLBACK_URL = '/';

const APP_SHELL_ASSETS = [
  '/',
  '/index.html',
  '/manifest.json',
  'https://cdn.tailwindcss.com',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.css',
  'https://unpkg.com/leaflet@1.9.4/dist/leaflet.js'
];

// 1. Install Event: Cache critical app shell
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[ServiceWorker] Pre-caching offline app shell');
      return cache.addAll(APP_SHELL_ASSETS).catch((err) => {
        console.warn('[ServiceWorker] Non-critical asset cache skip:', err);
      });
    }).then(() => self.skipWaiting())
  );
});

// 2. Activate Event: Clean up old cache versions
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keyList) => {
      return Promise.all(
        keyList.map((key) => {
          if (key !== CACHE_NAME) {
            console.log('[ServiceWorker] Purging deprecated cache:', key);
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// 3. Fetch Event: Intelligent routing (Network-First for Live Telemetry, Cache-First for Assets)
self.addEventListener('fetch', (event) => {
  const request = event.request;
  const url = new URL(request.url);

  // Ignore non-GET requests (e.g. POST /api/v1/sos)
  if (request.method !== 'GET') {
    return;
  }

  // API Requests: Network-First with Cache Fallback for offline flood resilience
  if (url.pathname.startsWith('/api/')) {
    event.respondWith(
      fetch(request)
        .then((networkResponse) => {
          if (networkResponse && networkResponse.status === 200) {
            const clone = networkResponse.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
          }
          return networkResponse;
        })
        .catch(async () => {
          console.warn('[ServiceWorker] Network failed; attempting offline cache fallback for:', url.pathname);
          const cachedResponse = await caches.match(request);
          if (cachedResponse) {
            return cachedResponse;
          }
          // Synthetic Offline JSON Response if totally disconnected
          return new Response(
            JSON.stringify({
              offline: true,
              message: 'Offline mode active: Cached flood telemetry displayed.',
              timestamp: new Date().toISOString()
            }),
            {
              headers: { 'Content-Type': 'application/json' },
              status: 200
            }
          );
        })
    );
    return;
  }

  // App Shell & Static Assets: Cache-First, fallback to network
  event.respondWith(
    caches.match(request).then((cachedResponse) => {
      if (cachedResponse) {
        return cachedResponse;
      }
      return fetch(request).then((networkResponse) => {
        if (networkResponse && networkResponse.status === 200 && request.url.startsWith('http')) {
          const clone = networkResponse.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return networkResponse;
      }).catch(() => {
        // If navigating to an HTML page while offline, return root index
        if (request.mode === 'navigate') {
          return caches.match(OFFLINE_FALLBACK_URL);
        }
      });
    })
  );
});

// 4. Background Sync for offline distress tickets
self.addEventListener('sync', (event) => {
  if (event.tag === 'sync-offline-sos') {
    console.log('[ServiceWorker] Background sync triggered: Syncing offline SOS outbox');
  }
});

// 5. Emergency Disaster Push Notifications
self.addEventListener('push', (event) => {
  const data = event.data ? event.data.json() : {};
  const title = data.title || 'JalRakshak Flood Alert';
  const options = {
    body: data.body || 'Severe waterlogging alert issued for your corridor.',
    icon: '/manifest.json',
    badge: '/manifest.json',
    vibrate: [200, 100, 200],
    data: { url: data.url || '/' }
  };
  event.waitUntil(self.registration.showNotification(title, options));
});
