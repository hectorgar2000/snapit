// SnapIT Service Worker — offline-first para la shell de la app
const CACHE = 'snapit-v1';
const SHELL = ['/app'];

self.addEventListener('install', e => {
  e.waitUntil(
    caches.open(CACHE).then(c => c.addAll(SHELL))
  );
  self.skipWaiting();
});

self.addEventListener('activate', e => {
  // Borrar cachés antiguas
  e.waitUntil(
    caches.keys().then(keys =>
      Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', e => {
  const url = new URL(e.request.url);

  // Dejar pasar peticiones a la API sin cachear
  const isAPI = ['/register','/login','/me','/today','/week','/submit',
                 '/feed','/leaderboard','/friends','/user/','/submission/','/guest']
    .some(p => url.pathname.startsWith(p));

  if (isAPI || e.request.method !== 'GET') return;

  // Para navegación: red primero, caché como fallback
  if (e.request.mode === 'navigate') {
    e.respondWith(
      fetch(e.request).catch(() => caches.match('/app'))
    );
    return;
  }

  // Para el resto (static assets): caché primero
  e.respondWith(
    caches.match(e.request).then(cached => cached || fetch(e.request))
  );
});
