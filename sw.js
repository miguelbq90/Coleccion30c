// Guarda la app en el aparato para que abra sin internet.
// Si subes una versión nueva de los archivos, cambia el número de CACHE (v10 -> v11).
// Cada copia de la app (la normal y la de /prueba/) usa su propia caché para no pisarse.
const CACHE = 'coleccion30c-v10@' + self.registration.scope;
const IMGS = 'coleccion30c-fotos-v1';
const SHELL = ['./', './index.html', './app30c.webmanifest', './icono30c-192.png', './icono30c-512.png', './icono30c-maskable.png', './icono30c-apple.png',
  './fonts/dmsans.woff', './fonts/montserrat.woff', './fonts/poppins-bold.woff', './fonts/archivoblack.woff'];

self.addEventListener('install', e => {
  e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', e => {
  e.waitUntil(
    caches.keys()
      .then(keys => Promise.all(keys.filter(k => k !== CACHE && k.endsWith('@' + self.registration.scope)).map(k => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', e => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const url = new URL(req.url);

  // Fotos de las cartas: si ya se vio, sale del aparato (vale sin conexión); si no, se baja y se guarda.
  if (url.hostname === 'images.scrydex.com') {
    e.respondWith((async () => {
      const c = await caches.open(IMGS);
      const hit = await c.match(req);
      if (hit) return hit;
      try {
        const res = await fetch(req);
        if (res && (res.ok || res.type === 'opaque')) c.put(req, res.clone()).catch(() => {});
        return res;
      } catch (err) {
        return new Response('', { status: 504, statusText: 'Sin conexión' });
      }
    })());
    return;
  }

  if (url.origin !== self.location.origin) return; // GitHub y demás: siempre por internet
  if (url.pathname.endsWith('/version.json')) return; // el aviso de versión nueva siempre va por internet
  if (url.pathname.endsWith('/precios.json')) return; // los precios: siempre por internet (la app guarda la última copia)

  // La app: primero lo guardado (rápido y sin conexión); por detrás se baja la versión nueva.
  // no-cache: pregunta siempre al servidor si hay versión nueva (si no la hay, no se descarga nada)
  const fresh = fetch(req.url, { cache: 'no-cache', credentials: 'same-origin' }).then(async res => {
    if (res && res.ok) {
      const copy = res.clone();
      const c = await caches.open(CACHE);
      await c.put(req, copy);
    }
    return res;
  }).catch(() => null);
  e.waitUntil(fresh.then(() => {}));

  e.respondWith((async () => {
    const c = await caches.open(CACHE);
    const hit = await c.match(req, { ignoreSearch: true });
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
