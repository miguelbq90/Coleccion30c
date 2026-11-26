# Saca las capturas de las maquetas. En GitHub usa el catálogo real; aquí (FALSO=1) usa relleno.
import os,sys,json,re,shutil,subprocess,time,pathlib,hashlib,io
from playwright.sync_api import sync_playwright
RAIZ=pathlib.Path(sys.argv[1]);OUT=pathlib.Path(sys.argv[2]);OUT.mkdir(parents=True,exist_ok=True)
MAQ=pathlib.Path(__file__).parent;FALSO=os.environ.get('FALSO')=='1';CHROME=os.environ.get('CHROME','/usr/bin/google-chrome')
site=pathlib.Path('/tmp/maq-site');shutil.rmtree(site,ignore_errors=True);site.mkdir()
for n in ['index.html','sw.js','version.json','precios.json','app30c.webmanifest']:shutil.copy(RAIZ/n,site/n)
shutil.copytree(RAIZ/'fonts',site/'fonts')
for p in RAIZ.glob('icono30c-*.png'):shutil.copy(p,site/p.name)
s=(site/'index.html').read_text(encoding='utf-8')
s=s.replace('</style>',(MAQ/'mk.css').read_text(encoding='utf-8')+'</style>',1)
s=s.replace('</body>','<script>'+(MAQ/'mk.js').read_text(encoding='utf-8')+'</script>\n</body>',1)
(site/'index.html').write_text(s,encoding='utf-8')
srv=subprocess.Popen([sys.executable,'-m','http.server','8899','-d',str(site)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL);time.sleep(1.2)
def falso(ctx):
    from PIL import Image,ImageDraw
    def png(w,h,txt,col):
        im=Image.new('RGBA',(w,h),(0,0,0,0));d=ImageDraw.Draw(im);d.rounded_rectangle((2,2,w-2,h-2),radius=h//3,fill=col);d.text((w//6,h//3),txt,fill=(255,255,255,255));b=io.BytesIO();im.save(b,'PNG');return b.getvalue()
    sets=[('sv10.5','30th Celebration'),('sv08.5','Prismatic Evolutions'),('sv08','Surging Sparks'),('sv03.5','151'),('sv03','Obsidian Flames'),('sv05','Temporal Forces'),('sv04.5','Paldean Fates')]
    def api(route):
        u=route.request.url
        if u.endswith('/en/sets'):return route.fulfill(json=[{'id':i,'name':n} for i,n in sets])
        m=re.search(r'/(en|es)/sets/([^/?]+)$',u);i=m.group(2)
        return route.fulfill(json={'id':i,'name':dict(sets)[i],'logo':f'https://assets.tcgdex.net/en/sv/{i}/logo','symbol':f'https://assets.tcgdex.net/univ/sv/{i}/symbol','serie':{'name':'Escarlata y Púrpura'},'cardCount':{'official':3},'cards':[{'localId':str(k),'image':f'https://assets.tcgdex.net/en/sv/{i}/{k}'} for k in range(1,6)]})
    def asset(route):
        u=route.request.url;h=int(hashlib.md5(u.encode()).hexdigest(),16)
        if 'logo' in u:return route.fulfill(body=png(360,120,'LOGO '+u.split('/')[-2],(200,(h%5)*50,120,255)),content_type='image/png')
        if 'symbol' in u:return route.fulfill(body=png(60,60,'S',(255,255,255,255)),content_type='image/png')
        return route.fulfill(body=(pathlib.Path('/home/claude/v20')/f'f{h%12}.jpg').read_bytes(),content_type='image/jpeg')
    ctx.route('**api.tcgdex.net/**',api);ctx.route('**assets.tcgdex.net/**',asset)
    ctx.route('**images.scrydex.com/**',lambda r:r.fulfill(body=(pathlib.Path('/home/claude/v20')/'f3.jpg').read_bytes(),content_type='image/jpeg'))
with sync_playwright() as p:
    b=p.chromium.launch(executable_path=CHROME)
    for m in ['M1','M2','M3','H1','H2','HS']:
        ctx=b.new_context(viewport={'width':390,'height':844},device_scale_factor=2,service_workers='block')
        if FALSO:falso(ctx)
        ctx.route('**googleapis.com/**',lambda r:r.abort())
        pg=ctx.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)))
        pg.goto('http://localhost:8899/');pg.evaluate("localStorage.setItem('c30-visto','999');localStorage.setItem('c30-estado',JSON.stringify({v:2,cards:Object.fromEntries(['001','002','004','005','008','012','013','020','149'].map(i=>[i,{o:1,t:1}])),goal:{}}))")
        pg.reload();pg.wait_for_timeout(2500)
        pg.evaluate(f"mk('{m}')")
        if m=='HS':
            y=pg.evaluate("document.getElementById('grid').getBoundingClientRect().top+scrollY");pg.evaluate(f"scrollTo(0,{y}+300)")
        try:pg.wait_for_load_state('networkidle',timeout=15000)
        except Exception:pass
        pg.wait_for_timeout(2500)
        pg.screenshot(path=str(OUT/f'{m}.png'))
        if m=='M1':(OUT/'catalogo.json').write_text(json.dumps(pg.evaluate('MKLOG'),ensure_ascii=False,indent=1),encoding='utf-8')
        print(m,'errores:',errs);ctx.close()
    b.close()
srv.terminate()
