# Temporal (rama «prueba»): capturas de la versión 23 en iPhone, iPad y ordenador, con fotos reales,
# y vídeo del sobre abriéndose (fotograma a fotograma). Las capturas se guardan en prueba/out.
import json, pathlib, shutil, subprocess, sys, time
from playwright.sync_api import sync_playwright
OUT = pathlib.Path('prueba/out'); shutil.rmtree(OUT, ignore_errors=True); OUT.mkdir(parents=True)
srv = subprocess.Popen([sys.executable, '-m', 'http.server', '8899'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL); time.sleep(1.2)
URL = 'http://localhost:8899/'
now = int(time.time() * 1000)
COLS = ['sv08.5', 'sv08', 'sv03.5', 'sv03', 'sv05', 'sv04.5', 'me02.5']
cards = {f'{i:03d}': {'o': 1, 't': now} for i in range(1, 41)}
for sid, n in (('sv03.5', 120), ('sv08.5', 60), ('me02.5', 25), ('sv08', 12)):
    sets = json.loads(pathlib.Path(f'precios/sets/{sid}.json').read_text())
    for c in sets['cartas'][:n]: cards[f'{sid}-{c[0]}'] = {'o': 1, 't': now}
ST = {'v': 3, 'cards': cards, 'goal': {'list': ['main', 'sec', 'rgb', 'cls'], 't': 0}, 'cols': {c: {'on': 1, 't': now} for c in COLS}, 'metas': {}}
INIT = f"try{{if(!localStorage.getItem('c30-estado'))localStorage.setItem('c30-estado',{json.dumps(json.dumps(ST))});if(!localStorage.getItem('c30-visto'))localStorage.setItem('c30-visto','23')}}catch(e){{}}"
log = []
def espera(pg, ms=2500):
    try: pg.wait_for_load_state('networkidle', timeout=15000)
    except Exception: pass
    pg.wait_for_timeout(ms)
def toca(pg, sel, tactil):
    (pg.tap if tactil else pg.click)(sel)
def recorrido(b, nombre, opciones, tactil):
    ctx = b.new_context(**opciones); ctx.add_init_script(INIT)
    pg = ctx.new_page(); errs = []
    pg.on('pageerror', lambda e: errs.append(str(e)))
    pg.goto(URL); espera(pg, 3000)
    pg.screenshot(path=str(OUT / f'{nombre}-1-cabecera.png'))
    toca(pg, '#pkHead', tactil); pg.wait_for_timeout(1250); pg.screenshot(path=str(OUT / f'{nombre}-2-rasgando.png'))
    pg.wait_for_timeout(2200); pg.screenshot(path=str(OUT / f'{nombre}-3-abierto.png'))
    fan = pg.eval_on_selector_all('#cmPk .sc', 'e=>e.length')
    toca(pg, '#cmTodas', tactil); espera(pg, 2000); pg.screenshot(path=str(OUT / f'{nombre}-4-lista.png'))
    filas = pg.eval_on_selector_all('#clista .cl-row', 'e=>e.length')
    if nombre == 'iphone':
        pg.fill('#clBus', 'llamas'); pg.wait_for_timeout(600); pg.screenshot(path=str(OUT / f'{nombre}-5-lista-buscar.png')); pg.fill('#clBus', '')
        pg.evaluate("document.getElementById('clista').scrollTop=9999"); pg.wait_for_timeout(500); pg.screenshot(path=str(OUT / f'{nombre}-5b-lista-abajo.png'))
    toca(pg, '#clAdd', tactil); espera(pg, 2500); pg.screenshot(path=str(OUT / f'{nombre}-6-anadir.png'))
    toca(pg, '#caBack', tactil); pg.wait_for_timeout(500)
    toca(pg, '#clista [data-col="me02.5"]', tactil); espera(pg, 3500)
    pg.screenshot(path=str(OUT / f'{nombre}-7-heroes.png'))
    n295 = pg.eval_on_selector_all('.p', 'e=>e.length')
    pg.evaluate("document.querySelector('.sect').scrollIntoView({block:'start'});window.scrollBy(0,-150)"); espera(pg, 2500)
    pg.screenshot(path=str(OUT / f'{nombre}-8-cartas.png'))
    pg.evaluate("const d=document.getElementById('apDiario');d.open=true;d.scrollIntoView({block:'start'});window.scrollBy(0,-130)"); espera(pg, 2500)
    pg.screenshot(path=str(OUT / f'{nombre}-9-diario.png'))
    diario = pg.text_content('#diario')[:120]
    log.append(f'{nombre}: sobre con {fan} colecciones · lista con {filas} filas · Héroes Ascendentes con {n295} cartas · diario: {diario!r} · errores: {errs}')
    if nombre == 'iphone':
        c2 = b.new_context(**opciones)
        c2.add_init_script(f"try{{localStorage.setItem('c30-estado',{json.dumps(json.dumps(ST))});localStorage.setItem('c30-visto','22')}}catch(e){{}}")
        p2 = c2.new_page(); p2.goto(URL); espera(p2, 2000); p2.screenshot(path=str(OUT / f'{nombre}-0-novedades.png')); c2.close()
    ctx.close()
with sync_playwright() as p:
    wk = p.webkit.launch()
    recorrido(wk, 'iphone', p.devices['iPhone 13'], True)
    recorrido(wk, 'iphone-se', p.devices['iPhone SE'], True)
    recorrido(wk, 'ipad', p.devices['iPad Pro 11'], True)
    recorrido(wk, 'ipad-horizontal', p.devices['iPad Pro 11 landscape'], True)
    wk.close()
    ch = p.chromium.launch()
    recorrido(ch, 'ordenador', {'viewport': {'width': 1366, 'height': 820}}, False)
    # Vídeo: fotograma a fotograma, en un móvil
    ctx = ch.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, has_touch=True, is_mobile=True); ctx.add_init_script(INIT)
    pg = ctx.new_page(); pg.goto(URL); espera(pg, 3000)
    fr = OUT / 'fr'; fr.mkdir()
    pg.click('#pkHead'); pg.wait_for_timeout(60)
    pg.evaluate("window.__an=document.getAnimations().filter(a=>a.effect&&a.effect.target&&a.effect.target.closest&&a.effect.target.closest('#cmenu'));__an.forEach(a=>a.pause())")
    n = 0
    for t in list(range(0, 3300, 40)) + [3300] * 14:
        pg.evaluate(f"__an.forEach(a=>{{try{{a.currentTime={t}}}catch(e){{}}}})"); pg.wait_for_timeout(12)
        pg.screenshot(path=str(fr / f'{n:03d}.png')); n += 1
    import imageio_ffmpeg
    subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-y', '-loglevel', 'error', '-framerate', '25', '-i', str(fr / '%03d.png'), '-vf', 'scale=780:-2', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '23', '-preset', 'veryfast', str(OUT / 'abrir-sobre.mp4')], check=True)
    shutil.rmtree(fr); ch.close()
srv.terminate()
(OUT / 'resultado.txt').write_text('\n'.join(log) + '\n', encoding='utf-8')
print('\n'.join(log))
