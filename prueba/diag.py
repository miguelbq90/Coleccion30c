# Diagnóstico temporal: ¿cargan las fotos de TCGdex en la web publicada, en un iPhone de prueba?
import json, pathlib, subprocess, urllib.request
from playwright.sync_api import sync_playwright
OUT = pathlib.Path('prueba/out'); OUT.mkdir(parents=True, exist_ok=True)
log = []
for u in ['https://assets.tcgdex.net/es/me/me02.5/001/low.webp', 'https://assets.tcgdex.net/es/me/me02.5/150/low.webp', 'https://assets.tcgdex.net/es/me/me02.5/001/high.webp', 'https://assets.tcgdex.net/es/sv/sv08.5/001/low.webp']:
    r = subprocess.run(['curl', '-sS', '-o', '/dev/null', '-D', '-', '-H', 'Referer: https://miguelbq90.github.io/', '-H', 'User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 18_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.0 Mobile/15E148 Safari/604.1', u], capture_output=True, text=True)
    log.append('CURL ' + u + '\n' + r.stdout + r.stderr)
WEB = 'https://miguelbq90.github.io/Coleccion30c/'
with sync_playwright() as p:
    for nombre, motor, disp in (('iphone', p.webkit, 'iPhone 13'), ('chrome', p.chromium, 'Pixel 7')):
        b = motor.launch(); ctx = b.new_context(**p.devices[disp]); pg = ctx.new_page()
        malas = []; errs = []
        pg.on('pageerror', lambda e: errs.append(str(e)))
        pg.on('response', lambda r: malas.append(f'{r.status} {r.url} {r.headers.get("content-type")} sw={r.from_service_worker}') if 'tcgdex' in r.url and r.status != 200 else None)
        pg.on('requestfailed', lambda r: malas.append(f'FALLO {r.url} {r.failure}') if 'tcgdex' in r.url else None)
        pg.goto(WEB, wait_until='load'); pg.wait_for_timeout(4000)
        pg.evaluate("localStorage.setItem('c30-visto','999')")
        pg.reload(wait_until='load'); pg.wait_for_timeout(4000)  # ya con el service worker al mando
        pg.tap('#pkHead'); pg.wait_for_timeout(3000); pg.tap('#cmenu [data-col="+"]'); pg.wait_for_timeout(3000)
        pg.tap('#cadd [data-add="me02.5"]'); pg.wait_for_timeout(6000)
        pg.evaluate("document.querySelector('.sect').scrollIntoView({block:'start'});window.scrollBy(0,-150)"); pg.wait_for_timeout(5000)
        pg.screenshot(path=str(OUT / f'{nombre}-heroes.png'))
        info = pg.evaluate("""(()=>{const im=[...document.querySelectorAll('.p img')];const vis=im.filter(i=>{const r=i.getBoundingClientRect();return r.top<innerHeight&&r.bottom>0});
          return {cartas:document.querySelectorAll('.p').length,imgs:im.length,visibles:vis.length,cargadas:vis.filter(i=>i.complete&&i.naturalWidth>0).length,ok:document.querySelectorAll('.p .ok, .p.ok').length,src:vis.slice(0,2).map(i=>i.currentSrc),sw:!!navigator.serviceWorker.controller}})()""")
        log.append(f'{nombre}: {json.dumps(info)} | errores JS {errs} | respuestas raras {malas[:10]}')
        b.close()
(OUT / 'diag.txt').write_text('\n'.join(log) + '\n', encoding='utf-8'); print('\n'.join(log))
