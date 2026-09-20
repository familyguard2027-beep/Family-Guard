const CACHE_NAME = 'family-guard-v5';
const ASSETS = [
  '/',
  '/static/css/app.css',
  '/static/js/app.js',
  '/static/icons/icon-192.png',
  '/static/icons/icon-512.png',
  '/manifest.json'
];

self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
  );
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys => Promise.all(keys
      .filter(key => key !== CACHE_NAME)
      .map(key => caches.delete(key))))
  );
  self.clients.claim();
});

self.addEventListener('fetch', event => {
  if (event.request.method !== 'GET') return;

  const requestUrl = new URL(event.request.url);
  const isNavigation = event.request.mode === 'navigate';
  const isLogin = requestUrl.pathname === '/login/';

  if (isNavigation || isLogin) {
    event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
    return;
  }

  const isStaticAsset = requestUrl.pathname.startsWith('/static/');
  if (isStaticAsset) {
    event.respondWith(fetch(event.request).then(response => {
      const copy = response.clone();
      caches.open(CACHE_NAME).then(cache => cache.put(event.request, copy));
      return response;
    }).catch(() => caches.match(event.request)));
    return;
  }

  event.respondWith(caches.match(event.request).then(cached => cached || fetch(event.request)));
});
