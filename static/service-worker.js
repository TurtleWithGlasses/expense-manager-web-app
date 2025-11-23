/**
 * Service Worker for BudgetPulse Expense Manager
 * Provides offline functionality, caching, and background sync
 */

const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `budgetpulse-${CACHE_VERSION}`;

// Assets to cache on install
const STATIC_ASSETS = [
  '/',
  '/static/css/themes.css',
  '/static/css/styles.css',
  '/static/css/accessibility.css',
  '/static/css/polish.css',
  '/static/css/advanced-features.css',
  '/static/css/nav-fix.css',
  '/static/css/bootstrap-icons.min.css',
  '/static/js/htmx.min.js',
  '/static/js/advanced-features.js',
  '/static/js/error-handling.js',
  '/static/fonts/bootstrap-icons.woff2',
  '/static/fonts/bootstrap-icons.woff',
  '/static/money_icon.png',
  '/static/manifest.json'
];

// API endpoints to cache (for offline access)
const API_CACHE_PATTERNS = [
  '/dashboard',
  '/entries',
  '/categories',
  '/settings'
];

// Network-first endpoints (always try network, fallback to cache)
const NETWORK_FIRST_PATTERNS = [
  '/api/',
  '/auth/'
];

// Cache-first assets (images, fonts, static files)
const CACHE_FIRST_PATTERNS = [
  '/static/',
  '.woff2',
  '.woff',
  '.ttf',
  '.png',
  '.jpg',
  '.jpeg',
  '.svg',
  '.ico'
];

/**
 * Install Event - Cache static assets
 */
self.addEventListener('install', (event) => {
  console.log('[Service Worker] Installing...');

  event.waitUntil(
    caches.open(CACHE_NAME)
      .then((cache) => {
        console.log('[Service Worker] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => {
        console.log('[Service Worker] Installation complete');
        return self.skipWaiting(); // Activate immediately
      })
      .catch((error) => {
        console.error('[Service Worker] Installation failed:', error);
      })
  );
});

/**
 * Activate Event - Clean up old caches
 */
self.addEventListener('activate', (event) => {
  console.log('[Service Worker] Activating...');

  event.waitUntil(
    caches.keys()
      .then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => {
            if (cacheName !== CACHE_NAME) {
              console.log('[Service Worker] Deleting old cache:', cacheName);
              return caches.delete(cacheName);
            }
          })
        );
      })
      .then(() => {
        console.log('[Service Worker] Activation complete');
        return self.clients.claim(); // Take control immediately
      })
  );
});

/**
 * Fetch Event - Implement caching strategies
 */
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip cross-origin requests
  if (url.origin !== location.origin) {
    return;
  }

  // Skip POST, PUT, DELETE requests (don't cache mutations)
  if (request.method !== 'GET') {
    return;
  }

  // Determine caching strategy
  if (shouldUseCacheFirst(url.pathname)) {
    event.respondWith(cacheFirst(request));
  } else if (shouldUseNetworkFirst(url.pathname)) {
    event.respondWith(networkFirst(request));
  } else {
    event.respondWith(networkFirst(request));
  }
});

/**
 * Check if URL should use cache-first strategy
 */
function shouldUseCacheFirst(pathname) {
  return CACHE_FIRST_PATTERNS.some(pattern => pathname.includes(pattern));
}

/**
 * Check if URL should use network-first strategy
 */
function shouldUseNetworkFirst(pathname) {
  return NETWORK_FIRST_PATTERNS.some(pattern => pathname.includes(pattern));
}

/**
 * Cache-First Strategy
 * Try cache first, fallback to network, update cache
 */
async function cacheFirst(request) {
  const cache = await caches.open(CACHE_NAME);
  const cached = await cache.match(request);

  if (cached) {
    console.log('[Service Worker] Cache hit:', request.url);
    // Return cached version and update in background
    updateCacheInBackground(request, cache);
    return cached;
  }

  console.log('[Service Worker] Cache miss, fetching:', request.url);
  try {
    const response = await fetch(request);
    if (response.ok) {
      cache.put(request, response.clone());
    }
    return response;
  } catch (error) {
    console.error('[Service Worker] Fetch failed:', error);
    return createOfflineResponse();
  }
}

/**
 * Network-First Strategy
 * Try network first, fallback to cache if offline
 */
async function networkFirst(request) {
  const cache = await caches.open(CACHE_NAME);

  try {
    const response = await fetch(request);

    if (response.ok) {
      // Update cache with fresh response
      cache.put(request, response.clone());
    }

    return response;
  } catch (error) {
    console.log('[Service Worker] Network failed, trying cache:', request.url);

    const cached = await cache.match(request);
    if (cached) {
      return cached;
    }

    // If no cache, return offline page
    return createOfflineResponse(request);
  }
}

/**
 * Update cache in background (stale-while-revalidate)
 */
function updateCacheInBackground(request, cache) {
  fetch(request)
    .then((response) => {
      if (response.ok) {
        cache.put(request, response.clone());
      }
    })
    .catch(() => {
      // Silently fail - we already have cached version
    });
}

/**
 * Create offline fallback response
 */
function createOfflineResponse(request) {
  const url = new URL(request.url);

  // For HTML pages, return offline page
  if (request.headers.get('accept').includes('text/html')) {
    return new Response(
      `
      <!DOCTYPE html>
      <html lang="en" data-theme="dark">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Offline - BudgetPulse</title>
        <style>
          body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1f2e;
            color: #e5e7eb;
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
            margin: 0;
            padding: 20px;
          }
          .container {
            text-align: center;
            max-width: 500px;
          }
          .icon {
            font-size: 64px;
            margin-bottom: 20px;
          }
          h1 {
            font-size: 24px;
            margin-bottom: 10px;
            color: #fff;
          }
          p {
            color: #9ca3af;
            margin-bottom: 30px;
            line-height: 1.6;
          }
          .btn {
            background: #3b82f6;
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            cursor: pointer;
            font-size: 16px;
            text-decoration: none;
            display: inline-block;
          }
          .btn:hover {
            background: #2563eb;
          }
        </style>
      </head>
      <body>
        <div class="container">
          <div class="icon">📡</div>
          <h1>You're Offline</h1>
          <p>
            It looks like you're not connected to the internet.
            Some features may not be available until you reconnect.
          </p>
          <button class="btn" onclick="window.location.reload()">
            Try Again
          </button>
        </div>
      </body>
      </html>
      `,
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: new Headers({
          'Content-Type': 'text/html; charset=utf-8'
        })
      }
    );
  }

  // For API requests, return JSON error
  if (url.pathname.startsWith('/api/')) {
    return new Response(
      JSON.stringify({
        success: false,
        error: 'offline',
        message: 'You are currently offline. This feature requires an internet connection.'
      }),
      {
        status: 503,
        statusText: 'Service Unavailable',
        headers: new Headers({
          'Content-Type': 'application/json'
        })
      }
    );
  }

  // Default offline response
  return new Response('Offline', { status: 503 });
}

/**
 * Background Sync - Sync failed requests when back online
 */
self.addEventListener('sync', (event) => {
  console.log('[Service Worker] Background sync:', event.tag);

  if (event.tag === 'sync-entries') {
    event.waitUntil(syncEntries());
  }
});

/**
 * Sync pending entries from IndexedDB when back online
 */
async function syncEntries() {
  console.log('[Service Worker] Syncing pending entries...');

  try {
    // This would sync with IndexedDB pending entries
    // For now, just log - full implementation would require IndexedDB integration
    console.log('[Service Worker] Sync completed');
  } catch (error) {
    console.error('[Service Worker] Sync failed:', error);
  }
}

/**
 * Push Notification Handler
 */
self.addEventListener('push', (event) => {
  console.log('[Service Worker] Push received');

  const data = event.data ? event.data.json() : {};
  const title = data.title || 'BudgetPulse';
  const options = {
    body: data.body || 'You have a new notification',
    icon: '/static/icons/icon-192x192.png',
    badge: '/static/icons/badge-72x72.png',
    vibrate: [200, 100, 200],
    tag: data.tag || 'notification',
    data: data.data || {},
    actions: data.actions || []
  };

  event.waitUntil(
    self.registration.showNotification(title, options)
  );
});

/**
 * Notification Click Handler
 */
self.addEventListener('notificationclick', (event) => {
  console.log('[Service Worker] Notification clicked:', event.notification.tag);

  event.notification.close();

  event.waitUntil(
    clients.openWindow(event.notification.data.url || '/')
  );
});

/**
 * Message Handler - Communication with main app
 */
self.addEventListener('message', (event) => {
  console.log('[Service Worker] Message received:', event.data);

  if (event.data && event.data.type === 'SKIP_WAITING') {
    self.skipWaiting();
  }

  if (event.data && event.data.type === 'CACHE_URLS') {
    const urls = event.data.urls || [];
    event.waitUntil(
      caches.open(CACHE_NAME).then((cache) => {
        return cache.addAll(urls);
      })
    );
  }

  if (event.data && event.data.type === 'CLEAR_CACHE') {
    event.waitUntil(
      caches.keys().then((cacheNames) => {
        return Promise.all(
          cacheNames.map((cacheName) => caches.delete(cacheName))
        );
      })
    );
  }
});

console.log('[Service Worker] Loaded successfully');
