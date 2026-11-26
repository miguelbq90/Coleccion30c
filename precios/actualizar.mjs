// Robot de precios de la app Colección 30C.
// Lo ejecuta GitHub una o dos veces al día (ver .github/workflows/precios.yml).
//
// Qué hace:
// 1. Descarga la guía de precios pública que Cardmarket publica cada día para Pokémon
//    (el mismo archivo que usan otras webs de precios; no entra en la web de Cardmarket).
// 2. Se queda solo con las 191 cartas de la colección (productos.json dice qué número
//    de producto de Cardmarket tiene cada carta).
// 3. Guarda el resultado en precios.json, que es lo que lee la app, junto con un pequeño
//    historial diario para ver si tu colección sube o baja.
//
// Ojo: Cardmarket da un precio de referencia que mezcla todos los idiomas.
// Para ver el precio de las cartas en español, la app abre Cardmarket ya filtrado en español.

import fs from 'node:fs';

const GUIA = 'https://downloads.s3.cardmarket.com/productCatalog/priceGuide/price_guide_6.json'; // 6 = Pokémon
const SALIDA = new URL('../precios.json', import.meta.url);
const PRODUCTOS = JSON.parse(fs.readFileSync(new URL('./productos.json', import.meta.url), 'utf8'));
const DIAS = 40; // días de historial que se guardan

export function construir(guia, previo, ahora = new Date()) {
  const porId = new Map((guia.priceGuides || []).map(g => [g.idProduct, g]));
  const r2 = x => (typeof x === 'number' && isFinite(x) && x > 0 ? Math.round(x * 100) / 100 : null);
  const ids = Object.keys(PRODUCTOS);
  const p = {};
  for (const id of ids) {
    const g = porId.get(PRODUCTOS[id]);
    if (!g) continue;
    // Las holo normales van en los campos sin sufijo; «-holo» en Cardmarket es la versión reverso.
    // Si una carta solo tiene precio en «-holo», se usa ese.
    const tieneNormal = [g.trend, g.avg, g.low, g.avg7, g.avg30].some(v => r2(v) !== null);
    const s = tieneNormal ? '' : '-holo';
    const e = { t: r2(g['trend' + s]), a1: r2(g['avg1' + s]), a7: r2(g['avg7' + s]), a30: r2(g['avg30' + s]), l: r2(g['low' + s]), a: r2(g['avg' + s]) };
    for (const k of Object.keys(e)) if (e[k] === null) delete e[k];
    if (Object.keys(e).length) p[id] = e;
  }
  const creado = typeof guia.createdAt === 'string' ? guia.createdAt : ahora.toISOString();
  const dia = creado.slice(0, 10);

  // Historial: un precio por carta y día (el de referencia), alineado con la lista «ids».
  let h = [];
  if (previo && Array.isArray(previo.h) && Array.isArray(previo.ids) && previo.ids.join() === ids.join()) h = previo.h.filter(x => x && x.d !== dia);
  const ref = e => (e ? e.t ?? e.a7 ?? e.a30 ?? e.a ?? e.l ?? null : null);
  h.push({ d: dia, t: ids.map(id => ref(p[id])) });
  h.sort((a, b) => (a.d < b.d ? -1 : 1));
  h = h.slice(-DIAS);

  return { v: 1, fuente: 'Cardmarket · guía de precios pública (media de todos los idiomas)', creado, generado: ahora.toISOString(), cartas: Object.keys(p).length, p, ids, h };
}

async function main() {
  let previo = null;
  try { previo = JSON.parse(fs.readFileSync(SALIDA, 'utf8')); } catch (e) {}

  const res = await fetch(GUIA, { headers: { 'User-Agent': 'coleccion30c-precios (app personal)' } });
  if (!res.ok) throw new Error('Cardmarket respondió ' + res.status);
  const guia = await res.json();
  try { fs.writeFileSync('/tmp/guia-cardmarket.json', JSON.stringify(guia)); } catch (e) {} // la reutiliza el robot de colecciones
  if (guia.version !== 1) console.warn('Aviso: versión de la guía de precios', guia.version);

  if (previo && previo.creado === guia.createdAt) {
    console.log('La guía de precios no ha cambiado desde', previo.creado, '· no hay nada que guardar');
    return;
  }
  const out = construir(guia, previo);
  if (out.cartas < 100) throw new Error('Solo he encontrado ' + out.cartas + ' cartas: algo raro pasa, no guardo nada');
  fs.writeFileSync(SALIDA, JSON.stringify(out) + '\n');
  console.log('Guardados los precios de', out.cartas, 'cartas · guía del', out.creado);
}

if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(e => { console.error(e); process.exit(1); });
}
