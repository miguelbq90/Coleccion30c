"""Vigilante de la app Zuroku (antes «Colección 30C»).

Lo ejecuta GitHub cada 6 horas, después de cada actualización de la app y después
de cada actualización de precios (ver .github/workflows/vigilante.yml).

Qué comprueba:
  1. Que la web publicada tiene la última versión de la app y los últimos precios.
     (Lo que falló el 25-11-2026: GitHub tuvo un error al publicar y la web se quedó atrás.)
  2. Que los precios no llevan más de 2 días sin actualizarse.
  3. Que la app funciona de verdad: la abre en un navegador, mira que salen las 191 cartas,
     los precios y que sigue funcionando sin internet.
  4. Que las fotos de las cartas cargan (eso depende de otro servidor: solo avisa).
  5. Que Firebase (cuentas y base de datos) funciona y que la base de datos está CERRADA
     a quien no tiene permiso (si alguien pudiera leerla sin cuenta, lo avisa como peligro).
  6. Que la app también va con el motor de Safari (el de iPhone y iPad): abre el sobre de
     colecciones y mira que salen.
  7. Que la lista de colecciones que se pueden añadir existe y está al día.

Cada revisión se apunta en el «diario» (rama «diario» del repositorio, archivo diario.json),
que Miguel puede leer desde la app: Ajustes › Diario del vigilante.

Si algo falla, primero intenta arreglarlo solo (volver a publicar la web o relanzar el robot
de precios). Si no lo consigue, abre un aviso («issue») en GitHub mencionando al dueño, y
GitHub le manda un correo. Cuando todo vuelve a ir bien, comenta y cierra el aviso.
"""
import base64
import datetime
import json
import os
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from zoneinfo import ZoneInfo

RAIZ = pathlib.Path(__file__).resolve().parent.parent
REPO = os.environ.get("REPO", "miguelbq90/Coleccion30c")
DUENO, NOMBRE = REPO.split("/")
WEB = (os.environ.get("SITE") or f"https://{DUENO.lower()}.github.io/{NOMBRE}/").rstrip("/") + "/"
API = os.environ.get("API", "https://api.github.com").rstrip("/")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
AVISAR = os.environ.get("AVISAR", DUENO)
CHROME = os.environ.get("CHROME", "/usr/bin/google-chrome")
INTENTOS = int(os.environ.get("ESPERA_INTENTOS", "10"))  # cuántas veces esperar a que GitHub publique
PAUSA = int(os.environ.get("ESPERA_SEG", "60"))  # segundos entre intentos
HOY = datetime.date.fromisoformat(os.environ["HOY"]) if os.environ.get("HOY") else datetime.datetime.now(datetime.timezone.utc).date()
REVISION = os.environ.get("RUN_URL", "")
FOTO = "https://images.scrydex.com/pokemon/me55-1/small"
TITULO = "⚠️ La app Zuroku necesita atención"
TITULOS_VIEJOS = ("⚠️ La app Colección 30C necesita atención",)
DIAS_MAX = 2

bien, arreglos, problemas, avisos = [], [], [], []
registro = []  # para el diario: (tema, tipo, texto)
TEMAS = {"revisar_web": "web", "revisar_precios": "precios", "revisar_app": "app", "revisar_iphone": "iphone",
         "revisar_fotos": "fotos", "revisar_firebase": "firebase", "revisar_colecciones": "colecciones"}


def descargar(url, cabeceras=None, tiempo=30):
    req = urllib.request.Request(url, headers={"User-Agent": "coleccion30c-vigilante", "Cache-Control": "no-cache", **(cabeceras or {})})
    with urllib.request.urlopen(req, timeout=tiempo) as r:
        return r.status, r.read()


def web_json(ruta):
    _, datos = descargar(f"{WEB}{ruta}?vigilante={int(time.time() * 1000)}")
    return json.loads(datos)


def github(metodo, ruta, cuerpo=None):
    datos = json.dumps(cuerpo).encode() if cuerpo is not None else None
    req = urllib.request.Request(API + ruta, data=datos, method=metodo, headers={
        "Accept": "application/vnd.github+json", "Authorization": f"Bearer {TOKEN}",
        "X-GitHub-Api-Version": "2022-11-28", "User-Agent": "coleccion30c-vigilante",
        **({"Content-Type": "application/json"} if datos else {})})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            txt = r.read()
            return r.status, (json.loads(txt) if txt else None)
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception as e:  # sin conexión con GitHub
        print("Error hablando con GitHub:", e)
        return 0, None


def leer_local(nombre):
    return json.loads((RAIZ / nombre).read_text(encoding="utf-8"))


# ---------- 1. ¿La web publicada está al día? ----------
def estado_web():
    ultima = leer_local("version.json")["build"]
    precios = leer_local("precios.json").get("generado", "")
    try:
        v = web_json("version.json")["build"]
        g = web_json("precios.json").get("generado", "")
    except Exception as e:
        return False, f"no se puede abrir la web ({e})"
    if v < ultima:
        return False, f"la web tiene la versión {v} y la última es la {ultima}"
    if g < precios:
        return False, "la web tiene unos precios más antiguos que los guardados"
    return True, f"la web tiene la versión {v} y los últimos precios"


def esperar_web():
    msg = ""
    for i in range(INTENTOS):
        ok, msg = estado_web()
        if ok:
            return True, msg
        if i < INTENTOS - 1:
            print(f"Aún no: {msg}. Espero {PAUSA} s (puede que GitHub esté publicando)…")
            time.sleep(PAUSA)
    return False, msg


def volver_a_publicar():
    s, _ = github("POST", f"/repos/{REPO}/pages/builds")
    if s in (200, 201):
        return "He pedido a GitHub que vuelva a publicar la web."
    # Plan B: un «commit» vacío también hace que GitHub vuelva a publicar.
    try:
        subprocess.run(["git", "config", "user.name", "github-actions[bot]"], cwd=RAIZ, check=True)
        subprocess.run(["git", "config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com"], cwd=RAIZ, check=True)
        subprocess.run(["git", "commit", "--allow-empty", "-m", "Vigilante: volver a publicar la web"], cwd=RAIZ, check=True)
        subprocess.run(["git", "push", "origin", "HEAD:main"], cwd=RAIZ, check=True)
        return "He vuelto a lanzar la publicación de la web."
    except Exception as e:
        print("No he podido relanzar la publicación:", e)
        return None


def revisar_web():
    ok, msg = esperar_web()
    if ok:
        bien.append(msg[0].upper() + msg[1:] + ".")
        return
    print("La web no está al día:", msg)
    hecho = volver_a_publicar()
    if hecho:
        arreglos.append(hecho)
        ok, msg2 = esperar_web()
        if ok:
            arreglos.append(f"Arreglado: {msg2}.")
            return
        msg = msg2
    problemas.append(f"La web publicada no está al día: {msg}. Puede ser un fallo de GitHub (mira githubstatus.com).")


# ---------- 2. ¿Los precios son recientes? ----------
def revisar_precios():
    p = leer_local("precios.json")
    dia = datetime.date.fromisoformat(p["creado"][:10])
    dias = (HOY - dia).days
    if dias <= DIAS_MAX:
        bien.append(f"Precios de Cardmarket del {dia.isoformat()} ({p.get('cartas', len(p.get('p', {})))} cartas).")
        return
    s, _ = github("POST", f"/repos/{REPO}/actions/workflows/precios.yml/dispatches", {"ref": "main"})
    if s == 204:
        arreglos.append("He relanzado el robot de precios.")
    problemas.append(f"Los precios llevan {dias} días sin actualizarse (son del {dia.isoformat()}).")


# ---------- 3. ¿La app funciona de verdad? ----------
def revisar_app():
    from playwright.sync_api import sync_playwright
    total = len(leer_local("precios.json").get("p", {}))
    with sync_playwright() as p:
        try:
            nav = p.chromium.launch(executable_path=CHROME) if os.path.exists(CHROME) else p.chromium.launch(channel="chrome")
        except Exception:
            subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=False)
            nav = p.chromium.launch()
        ctx = nav.new_context(viewport={"width": 390, "height": 844})
        pg = ctx.new_page()
        errores = []
        pg.on("pageerror", lambda e: errores.append(str(e)))
        try:
            pg.goto(WEB, wait_until="load", timeout=60000)
            pg.wait_for_function("document.querySelectorAll('.p').length>=191", timeout=30000)
            cartas = pg.eval_on_selector_all(".p", "e=>e.length")
            version = pg.text_content("#verTxt")
            try:
                pg.wait_for_selector("#din:not([hidden])", timeout=30000)
                con_precio = pg.eval_on_selector_all(".pr", "e=>e.length")
            except Exception:
                con_precio = 0
            if con_precio < total:
                problemas.append(f"La app solo muestra precio en {con_precio} de {total} cartas.")
            # Sin internet: deja que el «service worker» guarde la app, corta la conexión y recarga
            pg.evaluate("Promise.race([navigator.serviceWorker.ready.then(()=>1),new Promise(r=>setTimeout(()=>r(0),20000))])")
            pg.reload(wait_until="load")
            pg.wait_for_timeout(3000)
            ctx.set_offline(True)
            pg.reload(wait_until="load", timeout=30000)
            pg.wait_for_function("document.querySelectorAll('.p').length>=191", timeout=20000)
            sin_red = pg.eval_on_selector_all(".p", "e=>e.length")
            ctx.set_offline(False)
            if cartas == 191 and sin_red == 191 and not errores:
                bien.append(f"La app (versión {version}) abre bien, enseña las 191 cartas, {con_precio} precios y funciona sin internet.")
            else:
                problemas.append(f"La app no se ve bien: {cartas} cartas con internet, {sin_red} sin internet" + (f", errores: {'; '.join(errores[:3])}" if errores else "") + ".")
        except Exception as e:
            problemas.append(f"La app no ha cargado bien en el navegador de prueba ({str(e).splitlines()[0][:200]})" + (f". Errores: {'; '.join(errores[:3])}" if errores else "."))
        finally:
            nav.close()


# ---------- 4. ¿Cargan las fotos de las cartas? (servidor externo: solo aviso) ----------
def revisar_fotos():
    try:
        s, datos = descargar(FOTO, tiempo=20)
        if s == 200 and len(datos) > 1000:
            bien.append("Las fotos de las cartas cargan bien.")
            return
    except Exception as e:
        print("Foto de prueba:", e)
    avisos.append("Las fotos de las cartas no cargan desde su servidor. No depende de tu app: mientras tanto se ven con el diseño de respaldo.")


# ---------- 5. ¿Firebase funciona y está cerrado a desconocidos? ----------
def revisar_firebase():
    m = re.search(r"const FBCFG=\{apiKey:'([^']*)',projectId:'([^']*)'\}", (RAIZ / "index.html").read_text(encoding="utf-8"))
    if not m or not m.group(1):
        return  # la app aún no usa Firebase
    clave, proyecto = m.group(1), m.group(2)
    # a) La clave y el acceso con correo funcionan: un intento con una cuenta que no existe debe responder «datos incorrectos»
    try:
        req = urllib.request.Request(
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={clave}",
            data=json.dumps({"email": "vigilante@example.invalid", "password": "no-existe-123", "returnSecureToken": True}).encode(),
            headers={"Content-Type": "application/json"}, method="POST")
        try:
            urllib.request.urlopen(req, timeout=20)
            msg = "OK"
        except urllib.error.HTTPError as e:
            msg = (json.loads(e.read() or b"{}").get("error") or {}).get("message", "")
    except Exception as e:
        avisos.append(f"No he podido comprobar Firebase ({str(e)[:120]}).")
        return
    if "API key" in msg or "API_KEY" in msg:
        problemas.append("La clave de Firebase que lleva la app no es válida.")
        return
    if msg.startswith("OPERATION_NOT_ALLOWED"):
        problemas.append("En Firebase está desactivado el acceso con correo y contraseña.")
        return
    # b) La base de datos existe y NO deja leer a quien no tiene cuenta
    try:
        urllib.request.urlopen(f"https://firestore.googleapis.com/v1/projects/{proyecto}/databases/(default)/documents/colecciones/vigilante", timeout=20)
        problemas.append("¡Peligro! La base de datos deja leer sin cuenta: revisa las reglas de seguridad.")
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", "replace")
        if e.code in (401, 403):
            bien.append("Firebase funciona y la base de datos está cerrada a quien no tiene permiso.")
        elif e.code == 404 and "database" in cuerpo and "does not exist" in cuerpo:
            problemas.append("Falta crear la base de datos Firestore en Firebase.")
        elif e.code == 404:
            problemas.append("¡Peligro! La base de datos deja consultar sin cuenta: revisa las reglas de seguridad.")
        else:
            avisos.append(f"Firestore respondió {e.code} al comprobarlo.")
    except Exception as e:
        avisos.append(f"No he podido comprobar la base de datos ({str(e)[:120]}).")


# ---------- 6. ¿Funciona en el motor de Safari (iPhone y iPad)? ----------
def revisar_iphone():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        try:
            nav = p.webkit.launch()
        except Exception as e:
            avisos.append("Hoy no he podido abrir el navegador de prueba de iPhone (es un fallo del robot, no de tu app).")
            print("WebKit:", e)
            return
        try:
            ctx = nav.new_context(**p.devices["iPhone 13"])
            pg = ctx.new_page()
            errores = []
            pg.on("pageerror", lambda e: errores.append(str(e)))
            pg.goto(WEB, wait_until="load", timeout=60000)
            pg.wait_for_function("document.querySelectorAll('.p').length>=191", timeout=30000)
            pg.tap("#pkHead")
            pg.wait_for_timeout(3200)
            salen = pg.eval_on_selector_all("#cmPk .sc", "e=>e.length")
            pg.tap("#cmX")
            if salen >= 1 and not errores:
                bien.append(f"En un iPhone de prueba (motor de Safari) la app abre bien y el sobre se abre con {salen} {'colecciones' if salen > 1 else 'colección'} dentro.")
            else:
                problemas.append(f"En el iPhone de prueba el sobre no se abre bien ({salen} colecciones)" + (f". Errores: {'; '.join(errores[:3])}" if errores else "."))
        except Exception as e:
            problemas.append(f"En el iPhone de prueba la app no ha cargado bien ({str(e).splitlines()[0][:200]}).")
        finally:
            nav.close()


# ---------- 7. ¿Está al día la lista de colecciones que se pueden añadir? ----------
def revisar_colecciones():
    try:
        j = web_json("precios/sets/index.json")
    except Exception as e:
        avisos.append(f"No he podido abrir la lista de colecciones para añadir ({str(e)[:120]}).")
        return
    lista = j.get("colecciones") or []
    dia = datetime.date.fromisoformat((j.get("creado") or "2000-01-01")[:10])
    dias = (HOY - dia).days
    if len(lista) < 5:
        problemas.append(f"La lista de colecciones para añadir solo tiene {len(lista)}.")
        return
    try:
        uno = web_json(f"precios/sets/{lista[0]['id']}.json")
        assert len(uno.get("cartas") or []) > 10
    except Exception:
        problemas.append(f"La colección «{lista[0].get('nombre')}» no se puede descargar bien.")
        return
    if dias > DIAS_MAX:
        avisos.append(f"Los precios de las colecciones del catálogo son del {dia.isoformat()} (llevan {dias} días sin actualizarse).")
    else:
        bien.append(f"Hay {len(lista)} colecciones para añadir, con precios del {dia.isoformat()}.")


# ---------- Diario: lo que ve en cada revisión, para leerlo desde la app ----------
def guardar_diario():
    if not TOKEN:
        return
    madrid = datetime.datetime.now(ZoneInfo("Europe/Madrid"))
    padre, diario = None, {"v": 1, "dias": [], "notas": []}
    s, ref = github("GET", f"/repos/{REPO}/git/ref/heads/diario")
    if s == 200 and ref:
        padre = ref["object"]["sha"]
        s2, c = github("GET", f"/repos/{REPO}/contents/diario.json?ref=diario")
        if s2 == 200 and c:
            try:
                diario = json.loads(base64.b64decode(c["content"]).decode("utf-8"))
            except Exception as e:
                print("Diario ilegible, empiezo uno nuevo:", e)
    por = {"schedule": "revisión de cada 6 horas", "push": "tras una actualización de la app",
           "workflow_dispatch": "a petición (precios nuevos o a mano)"}.get(os.environ.get("GITHUB_EVENT_NAME", ""), "revisión")
    entrada = {"h": madrid.strftime("%H:%M"), "ok": not problemas, "por": por,
               "it": [{"k": k, "s": t, "m": m} for k, t, m in registro], **({"url": REVISION} if REVISION else {})}
    hoy = madrid.date().isoformat()
    dias = [d for d in diario.get("dias", []) if d.get("d") != hoy]
    dia = next((d for d in diario.get("dias", []) if d.get("d") == hoy), {"d": hoy, "r": []})
    dia["r"] = (dia.get("r") or [])[-11:] + [entrada]
    limite = (madrid.date() - datetime.timedelta(days=30)).isoformat()
    diario["dias"] = sorted([d for d in dias if d.get("d", "") >= limite] + [dia], key=lambda d: d["d"], reverse=True)
    diario["actualizado"] = madrid.isoformat(timespec="minutes")
    texto = json.dumps(diario, ensure_ascii=False, indent=1) + "\n"
    s, arbol = github("POST", f"/repos/{REPO}/git/trees", {"tree": [{"path": "diario.json", "mode": "100644", "type": "blob", "content": texto}]})
    if s != 201:
        print("No he podido guardar el diario (árbol):", s)
        return
    s, com = github("POST", f"/repos/{REPO}/git/commits", {"message": f"Diario: revisión del {hoy} a las {entrada['h']}", "tree": arbol["sha"], "parents": [padre] if padre else []})
    if s != 201:
        print("No he podido guardar el diario (commit):", s)
        return
    if padre:
        s, _ = github("PATCH", f"/repos/{REPO}/git/refs/heads/diario", {"sha": com["sha"]})
    else:
        s, _ = github("POST", f"/repos/{REPO}/git/refs", {"ref": "refs/heads/diario", "sha": com["sha"]})
    print("Diario guardado" if s in (200, 201) else f"No he podido guardar el diario (rama): {s}")


# ---------- Aviso en GitHub ----------
def avisar():
    s, lista = github("GET", f"/repos/{REPO}/issues?state=open&per_page=50")
    abierto = next((i for i in (lista or []) if i.get("title") in (TITULO, *TITULOS_VIEJOS) and "pull_request" not in i), None)
    enlace = f"\n\n[Ver esta revisión]({REVISION})" if REVISION else ""
    if problemas:
        texto = ("He encontrado algo que no va bien en tu app:\n\n" + "\n".join(f"- ❌ {x}" for x in problemas)
                 + ("\n\n**Lo que he intentado yo solo:**\n" + "\n".join(f"- 🔧 {x}" for x in arreglos) if arreglos else "")
                 + ("\n\n" + "\n".join(f"- ⚠️ {x}" for x in avisos) if avisos else "")
                 + "\n\nVolveré a mirarlo en unas horas. Cuando se arregle, cerraré este aviso yo solo." + enlace)
        if abierto:
            github("POST", f"/repos/{REPO}/issues/{abierto['number']}/comments", {"body": "Sigue pasando:\n\n" + texto})
            print("Añadido comentario al aviso", abierto["number"])
        else:
            s, nuevo = github("POST", f"/repos/{REPO}/issues", {"title": TITULO, "body": f"@{AVISAR} " + texto})
            print("Aviso creado:", s, (nuevo or {}).get("html_url"))
    elif abierto:
        github("POST", f"/repos/{REPO}/issues/{abierto['number']}/comments", {"body": "✅ Todo vuelve a funcionar bien:\n\n" + "\n".join(f"- {x}" for x in bien + arreglos) + enlace})
        github("PATCH", f"/repos/{REPO}/issues/{abierto['number']}", {"state": "closed", "state_reason": "completed"})
        print("Aviso cerrado:", abierto["number"])


def resumen():
    lineas = ["## Revisión de la app Zuroku", ""]
    lineas += [f"- ✅ {x}" for x in bien] + [f"- 🔧 {x}" for x in arreglos] + [f"- ⚠️ {x}" for x in avisos] + [f"- ❌ {x}" for x in problemas]
    txt = "\n".join(lineas)
    print(txt)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(txt + "\n")


if __name__ == "__main__":
    for paso in (revisar_web, revisar_precios, revisar_app, revisar_iphone, revisar_fotos, revisar_firebase, revisar_colecciones):
        antes = {t: len(l) for t, l in (("ok", bien), ("arreglo", arreglos), ("aviso", avisos), ("mal", problemas))}
        try:
            paso()
        except Exception as e:
            problemas.append(f"Fallo inesperado del vigilante en «{paso.__name__}»: {e}")
        for t, l in (("ok", bien), ("arreglo", arreglos), ("aviso", avisos), ("mal", problemas)):
            registro += [(TEMAS.get(paso.__name__, "otro"), t, m) for m in l[antes[t]:]]
    resumen()
    avisar()
    try:
        guardar_diario()
    except Exception as e:
        print("No he podido guardar el diario:", e)
    sys.exit(1 if problemas else 0)
