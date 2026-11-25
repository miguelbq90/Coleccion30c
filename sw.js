// Guarda la app en el aparato para que abra sin internet.
// Si subes una versión nueva de los archivos, cambia el número de CACHE (v1 -> v2).
const CACHE = 'coleccion30c-v1';
const SHELL = ['./', './index.html', './manifest.webmanifest', './icon-192.png', './icon-512.png', './icon-maskable.png', './apple-touch-icon.png'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);
  const same = url.origin === self.location.origin;
  const font = /(^|\.)fonts\.(googleapis|gstatic)\.com$/.test(url.hostname);
  if (!same && !font) return; // GitHub y demás: siempre por internet

  // Primero lo guardado (rápido y sin conexión); por detrás se baja la versión nueva.
  const fresh = fetch(req).then(async res => {
    if (res && (res.ok || res.type === 'opaque')) {
      const copy = res.clone();
      const c = await caches.open(CACHE);
      await c.put(req, copy);
    }
    return res;
  }).catch(() => null);
  e.waitUntil(fresh.then(() => {}));

  e.respondWith((async () => {
    const c = await caches.open(CACHE);
    const hit = await c.match(req, { ignoreSearch: same });
    if (hit) return hit;
    const res = await fresh;
    if (res) return res;
    if (req.mode === 'navigate') {
      const idx = (await c.match('./index.html')) || (await c.match('./'));
      if (idx) return idx;
    }
    return new Response('', { status: 504, statusText: 'Sin conexión' });
  })());
});
