# Capturas del sobre realista y vídeo de la animación (fotograma a fotograma, sin saltos).
import os,sys,json,shutil,subprocess,time,pathlib,hashlib,io,re
from playwright.sync_api import sync_playwright
RAIZ=pathlib.Path(sys.argv[1]);OUT=pathlib.Path(sys.argv[2]);OUT.mkdir(parents=True,exist_ok=True)
MAQ=pathlib.Path(__file__).parent;FALSO=os.environ.get('FALSO')=='1';CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
ART=os.environ.get('ART','152');MODOS=os.environ.get('MODOS','CAND,SH,SA').split(',')
site=pathlib.Path('/tmp/maq-site');shutil.rmtree(site,ignore_errors=True);site.mkdir()
for n in ['index.html','sw.js','version.json','precios.json','app30c.webmanifest']:shutil.copy(RAIZ/n,site/n)
shutil.copytree(RAIZ/'fonts',site/'fonts')
for p in RAIZ.glob('icono30c-*.png'):shutil.copy(p,site/p.name)
s=(site/'index.html').read_text(encoding='utf-8')
css=(MAQ/'mk.css').read_text(encoding='utf-8')+(MAQ/'sobre2.css').read_text(encoding='utf-8')
s=s.replace('</style>',css+'</style>',1)
s=s.replace('</body>','<script>'+(MAQ/'sobre2.js').read_text(encoding='utf-8')+'</script><script>'+(MAQ/'mk.js').read_text(encoding='utf-8')+'</script>\n</body>',1)
(site/'index.html').write_text(s,encoding='utf-8')
srv=subprocess.Popen([sys.executable,'-m','http.server','8899','-d',str(site)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1.2)
sys.path.insert(0,str(MAQ))
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME)
    ctx=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,service_workers='block')
    ctx.add_init_script(f"window.MK_ART={json.dumps(ART)}")
    if FALSO:
        ph=pathlib.Path('/home/claude/v20')
        ctx.route('**/images.scrydex.com/**',lambda r:r.fulfill(body=(ph/f'f{int(hashlib.md5(r.request.url.encode()).hexdigest(),16)%12}.jpg').read_bytes(),content_type='image/jpeg'))
        ctx.route('**api.tcgdex.net/**',lambda r:r.fulfill(json=[] if r.request.url.endswith('/sets') else {}))
    ctx.route('**googleapis.com/**',lambda r:r.abort())
    for m in MODOS:
        pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto('http://localhost:8899/');pg.evaluate("localStorage.setItem('c30-visto','999');localStorage.setItem('c30-estado',JSON.stringify({v:2,cards:Object.fromEntries(['001','002','004','005','008','012','013','020','149'].map(i=>[i,{o:1,t:1}])),goal:{}}))")
        pg.reload();pg.wait_for_timeout(2500)
        pg.evaluate(f"mk('{m}')")
        try:pg.wait_for_load_state('networkidle',timeout=15000)
        except Exception:pass
        pg.wait_for_timeout(2500)
        if m=='SA':
            fr=OUT/'fr';shutil.rmtree(fr,ignore_errors=True);fr.mkdir()
            pg.evaluate("window.__an=document.getAnimations();__an.forEach(a=>a.pause())")
            n=0
            for t in list(range(0,3200,40))+[3200]*12:
                pg.evaluate(f"__an.forEach(a=>{{try{{a.currentTime={t}}}catch(e){{}}}})");pg.wait_for_timeout(15)
                pg.screenshot(path=str(fr/f'{n:03d}.png'));n+=1
            shutil.copy(fr/f'{n-1:03d}.png',OUT/'SA-final.png');shutil.copy(fr/'030.png',OUT/'SA-rasgando.png')
            try:
                subprocess.run(['ffmpeg','-y','-loglevel','error','-framerate','25','-i',str(fr/'%03d.png'),'-vf','scale=780:-2','-c:v','libx264','-pix_fmt','yuv420p','-crf','23','-preset','veryfast',str(OUT/'abrir-sobre.mp4')],check=True)
            except Exception as e: print('ffmpeg:',e)
            from PIL import Image
            ims=[Image.open(fr/f'{i:03d}.png').convert('RGB').resize((300,650)) for i in range(0,n,2)]
            ims[0].save(OUT/'abrir-sobre.gif',save_all=True,append_images=ims[1:],duration=80,loop=0,optimize=True)
            shutil.rmtree(fr)
        else:
            pg.screenshot(path=str(OUT/f'{m}.png'))
        print(m,'errores:',errs);pg.close()
    b.close()
srv.terminate()
