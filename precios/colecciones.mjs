// Robot de colecciones de Zuroku.
// Lo ejecuta GitHub junto al robot de precios (ver .github/workflows/precios.yml).
//
// Qué hace, en palabras sencillas:
// 1. Pregunta al catálogo abierto TCGdex qué colecciones hay en las series que sigue la app
//    (por ejemplo «Escarlata y Púrpura» y «Megaevolución»). Las nuevas aparecen solas.
// 2. Para cada colección guarda la lista de cartas (número, nombre, foto) en español,
//    con el inglés de reserva cuando falta algo.
// 3. Averigua una sola vez qué producto de Cardmarket es cada carta y lo apunta en precios/mapa/,
//    para no tener que volver a preguntarlo cada día.
// 4. Con la guía de precios pública de Cardmarket (la misma que usa el robot de precios),
//    escribe precios/sets/<colección>.json con las cartas y sus precios del día,
//    y precios/sets/index.json con la lista de colecciones que la app puede añadir.

import fs from 'node:fs';

const API = 'https://api.tcgdex.net/v2/';
const GUIA = 'https://downloads.s3.cardmarket.com/productCatalog/priceGuide/price_guide_6.json';
const AQUI = new URL('./', import.meta.url);
const CONF = JSON.parse(fs.readFileSync(new URL('./series.json', AQUI), 'utf8'));
const DIR_SETS = new URL('./sets/', AQUI), DIR_MAPA = new URL('./mapa/', AQUI);
fs.mkdirSync(DIR_SETS, { recursive: true }); fs.mkdirSync(DIR_MAPA, { recursive: true });
const MAX_CONSULTAS = +(process.env.MAX_CONSULTAS || 3000); // tope de fichas de carta por ejecución
const SOLO = (process.env.SOLO || '').split(',').filter(Boolean); // para pruebas: solo estas colecciones

const espera = ms => new Promise(r => setTimeout(r, ms));
let consultas = 0;
async function pide(ruta, intentos = 4) {
  for (let i = 0; i < intentos; i++) {
    try {
      const r = await fetch(API + ruta, { headers: { 'User-Agent': 'zuroku-colecciones (app personal)' } });
      if (r.status === 404) return null;
      if (r.status === 429 || r.status >= 500) { await espera(1500 * (i + 1)); continue; }
      if (!r.ok) throw new Error('TCGdex ' + r.status + ' en ' + ruta);
      return await r.json();
    } catch (e) { if (i === intentos - 1) throw e; await espera(1000 * (i + 1)); }
  }
  return null;
}
// Hace muchas peticiones a la vez, pero pocas (para no molestar al catálogo)
async function enParalelo(lista, n, fn) {
  const out = new Array(lista.length); let k = 0;
  await Promise.all(Array.from({ length: n }, async () => { while (k < lista.length) { const i = k++; out[i] = await fn(lista[i], i); } }));
  return out;
}
const leer = (url, def) => { try { return JSON.parse(fs.readFileSync(url, 'utf8')); } catch (e) { return def; } };
const r2 = x => (typeof x === 'number' && isFinite(x) && x > 0 ? Math.round(x * 100) / 100 : null);
const corto = s => String(s || '').replace(/\s+/g, ' ').trim();

export function precioDe(g) {
  if (!g) return null;
  const normal = [g.trend, g.avg, g.low, g.avg7, g.avg30].some(v => r2(v) !== null);
  const s = normal ? '' : '-holo';
  const e = { t: r2(g['trend' + s]), a7: r2(g['avg7' + s]), a30: r2(g['avg30' + s]), a: r2(g['avg' + s]) };
  for (const k of Object.keys(e)) if (e[k] === null) delete e[k];
  return Object.keys(e).length ? e : null;
}
const refDe = e => (e ? e.t ?? e.a7 ?? e.a30 ?? e.a ?? null : null);

async function main() {
  // 1. ¿Qué colecciones hay?
  const series = await pide('en/series') || [];
  const quiero = series.filter(s => CONF.series.some(n => n.toLowerCase() === String(s.name).toLowerCase()));
  console.log('Series que sigo:', quiero.map(s => s.id + ' · ' + s.name).join(' | ') || '(ninguna: revisa series.json)');
  let briefs = [];
  for (const s of quiero) {
    const d = await pide('en/series/' + s.id);
    for (const b of (d && d.sets) || []) briefs.push({ ...b, serieId: s.id });
  }
  const omitir = new RegExp(CONF.omitir || '^$', 'i');
  briefs = briefs.filter(b => !omitir.test(b.id) && ((b.cardCount && b.cardCount.official) || 0) >= (CONF.minimoCartas || 30));
  if (SOLO.length) briefs = briefs.filter(b => SOLO.includes(b.id));
  console.log('Colecciones:', briefs.length);

  // 2. Guía de precios de Cardmarket (la de hoy)
  let guia = null;
  try { guia = JSON.parse(fs.readFileSync('/tmp/guia-cardmarket.json', 'utf8')); } catch (e) {}
  if (!guia) {
    const r = await fetch(GUIA, { headers: { 'User-Agent': 'zuroku-colecciones (app personal)' } });
    if (!r.ok) throw new Error('Cardmarket respondió ' + r.status);
    guia = await r.json();
  }
  const porProducto = new Map((guia.priceGuides || []).map(g => [g.idProduct, g]));
  const creado = typeof guia.createdAt === 'string' ? guia.createdAt : new Date().toISOString();

  const indice = [];
  for (const b of briefs) {
    const [es, en] = await Promise.all([pide('es/sets/' + b.id), pide('en/sets/' + b.id)]);
    const base = en || es; if (!base) { console.log('  ', b.id, 'no responde; la salto'); continue; }
    const oficial = (base.cardCount && base.cardCount.official) || 0;
    const cardsEn = (en && en.cards) || [], cardsEs = new Map(((es && es.cards) || []).map(c => [c.localId, c]));
    // 3. Mapa carta → producto de Cardmarket (y rareza), guardado para no repetirlo
    const mapaUrl = new URL(b.id + '.json', DIR_MAPA);
    const mapa = leer(mapaUrl, {});
    const faltan = cardsEn.filter(c => !(c.id in mapa));
    const puedo = Math.max(0, MAX_CONSULTAS - consultas);
    const ahora = faltan.slice(0, puedo);
    consultas += ahora.length;
    if (ahora.length) {
      await enParalelo(ahora, 5, async c => {
        const f = await pide('en/cards/' + encodeURIComponent(c.id));
        const cm = f && f.pricing && f.pricing.cardmarket;
        mapa[c.id] = { p: (cm && (cm.idProduct || cm.productId)) || 0, r: corto(f && f.rarity) };
      });
      fs.writeFileSync(mapaUrl, JSON.stringify(mapa) + '\n');
      console.log('  ', b.id, 'fichas nuevas consultadas:', ahora.length, faltan.length > ahora.length ? `(quedan ${faltan.length - ahora.length} para la próxima)` : '');
    }
    // 4. Cartas y precios del día
    const cartas = [], p = {}, cm = {};
    let top = null;
    for (const c of cardsEn) {
      const e = cardsEs.get(c.localId);
      const nombreEs = corto(e && e.name), nombreEn = corto(c.name);
      const img = (e && e.image) || c.image || '';
      const m = mapa[c.id] || {};
      cartas.push([c.localId, nombreEs || nombreEn, nombreEs && nombreEs !== nombreEn ? nombreEn : '', img, m.r || '']);
      if (m.p) { cm[c.localId] = m.p; const pr = precioDe(porProducto.get(m.p)); if (pr) { p[c.localId] = pr; const v = refDe(pr); if (v != null && img && (!top || v > top.v)) top = { id: c.localId, v, img }; } }
    }
    const logo = (es && es.logo) || (en && en.logo) || '';
    const simbolo = (en && en.symbol) || (es && es.symbol) || '';
    const set = {
      v: 1, id: b.id, nombre: corto((es && es.name) || (en && en.name) || b.name), nombreEn: corto(en && en.name),
      serie: corto((es && es.serie && es.serie.name) || (en && en.serie && en.serie.name)), serieId: b.serieId,
      logo, logoEn: (en && en.logo) || '', simbolo, fecha: (base.releaseDate || '').slice(0, 10), oficial, total: cartas.length,
      creado, cartas, p, cm,
    };
    fs.writeFileSync(new URL(b.id + '.json', DIR_SETS), JSON.stringify(set) + '\n');
    indice.push({ id: set.id, nombre: set.nombre, nombreEn: set.nombreEn, serie: set.serie, serieId: set.serieId, logo, logoEn: set.logoEn, simbolo, fecha: set.fecha, oficial, total: set.total, conPrecio: Object.keys(p).length, portada: top ? top.img : (cartas[0] && cartas[0][3]) || '' });
    console.log('  ', b.id, set.nombre, '·', set.total, 'cartas ·', Object.keys(p).length, 'con precio');
  }
  if (!indice.length) throw new Error('No he podido preparar ninguna colección');
  // Se conservan en el índice las que ya estaban y hoy no respondieron (solo si siguen en la lista de las que quiero)
  const viejo = leer(new URL('index.json', DIR_SETS), { colecciones: [] });
  for (const x of viejo.colecciones || []) if (!indice.some(y => y.id === x.id) && briefs.some(b => b.id === x.id) && fs.existsSync(new URL(x.id + '.json', DIR_SETS)) && !SOLO.length) indice.push(x);
  indice.sort((a, b) => (a.fecha < b.fecha ? 1 : a.fecha > b.fecha ? -1 : 0));
  fs.writeFileSync(new URL('index.json', DIR_SETS), JSON.stringify({ v: 1, creado, generado: new Date().toISOString(), colecciones: indice }) + '\n');
  console.log('Índice:', indice.length, 'colecciones · fichas consultadas hoy:', consultas);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(e => { console.error(e); process.exit(1); });
}
