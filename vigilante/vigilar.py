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

Si algo falla, primero intenta arreglarlo solo (volver a publicar la web o relanzar el robot
de precios). Si no lo consigue, abre un aviso («issue») en GitHub mencionando al dueño, y
GitHub le manda un correo. Cuando todo vuelve a ir bien, comenta y cierra el aviso.
"""
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
    for paso in (revisar_web, revisar_precios, revisar_app, revisar_fotos, revisar_firebase):
        try:
            paso()
        except Exception as e:
            problemas.append(f"Fallo inesperado del vigilante en «{paso.__name__}»: {e}")
    resumen()
    avisar()
    sys.exit(1 if problemas else 0)
