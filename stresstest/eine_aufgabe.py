"""Fuehrt EINE Stresstest-Aufgabe aus: Browserfenster oeffnen, Screen-Helfer wie ein Nutzer
bedienen (Tastenkombi-Ablauf, Bereich aufziehen, ohne Nachfrage eintragen), Ergebnis ausgeben.
Aufruf: py eine_aufgabe.py <aufgabe> <seed>"""
import ctypes, ctypes.wintypes, json, os, shutil, subprocess, sys, tempfile, time

HIER = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HIER))
ctypes.windll.shcore.SetProcessDpiAwareness(2)
import screen_helfer as s

aufgabe, seed = sys.argv[1], sys.argv[2]
EDGE = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
PROFIL = os.path.join(tempfile.gettempdir(), "screenhelfer_stress_edge")
url = "file:///" + os.path.join(HIER, "stress.html").replace("\\", "/") + f"?t={aufgabe}&s={seed}"
u32 = ctypes.windll.user32


def fenster_finden():
    gefunden = []
    def cb(hwnd, _):
        puffer = ctypes.create_unicode_buffer(512)
        u32.GetWindowTextW(hwnd, puffer, 512)
        if puffer.value.startswith(("STRESS", "PRUEFEN")) and u32.IsWindowVisible(hwnd):
            gefunden.append(hwnd)
        return True
    u32.EnumWindows(ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)(cb), 0)
    return gefunden[0] if gefunden else None


def titel(hwnd):
    puffer = ctypes.create_unicode_buffer(2048)
    u32.GetWindowTextW(hwnd, puffer, 2048)
    return puffer.value


edge = subprocess.Popen([EDGE, f"--user-data-dir={PROFIL}", "--no-first-run", "--disable-sync",
                         "--no-default-browser-check", f"--app={url}",
                         "--window-position=640,40", "--window-size=900,880"])
hwnd = None
for _ in range(60):
    time.sleep(0.25)
    hwnd = fenster_finden()
    if hwnd:
        break
if not hwnd:
    print(json.dumps({"aufgabe": aufgabe, "seed": seed, "ergebnis": "BROWSER NICHT GEFUNDEN"}))
    sys.exit(1)
time.sleep(1.5)
# Browser an eine feste Stelle schieben, nach vorne holen (kein anderes Fenster darueber)
def raender():
    r = ctypes.wintypes.RECT()        # echte sichtbare Raender (ohne unsichtbaren Schatten-Rahmen)
    ctypes.windll.dwmapi.DwmGetWindowAttribute(ctypes.c_void_p(hwnd), 9, ctypes.byref(r), ctypes.sizeof(r))
    return (r.left, r.top, r.right, r.bottom)

# Edge setzt seine gespeicherte Fensterposition manchmal verspaetet -> so lange hinschieben,
# bis das Fenster 2 s lang stillsteht
# Bildschirm fuer den Test: der zweite Monitor, wenn vorhanden (dort stoert nichts), sonst der erste
monitore = []
def _mon(hmon, hdc, rect, _):
    rc = ctypes.cast(rect, ctypes.POINTER(ctypes.wintypes.RECT)).contents
    monitore.append((rc.left, rc.top, rc.right, rc.bottom))
    return True
u32.EnumDisplayMonitors(None, None, ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p,
                                                       ctypes.c_void_p, ctypes.c_void_p)(_mon), 0)
monitor = sorted(monitore)[-1]          # der rechteste Bildschirm
# Vollbild (maximiert) auf diesem Bildschirm; so lange wiederholen, bis das Fenster stillsteht
letzte = None
for _ in range(10):
    u32.ShowWindow(ctypes.c_void_p(hwnd), 9)                   # SW_RESTORE
    u32.SetWindowPos(ctypes.c_void_p(hwnd), ctypes.c_void_p(-1), monitor[0] + 50, monitor[1] + 50,
                     800, 600, 0x0040)
    u32.ShowWindow(ctypes.c_void_p(hwnd), 3)                   # SW_MAXIMIZE
    u32.SetForegroundWindow(ctypes.c_void_p(hwnd))
    time.sleep(2)
    jetzt = raender()
    if jetzt == letzte:
        break
    letzte = jetzt
r = ctypes.wintypes.RECT(*raender())
# Nur den Seiteninhalt nehmen: Titelleiste oben weg, kleiner Rand ringsum
bereich = (max(r.left, monitor[0]) + 4, max(r.top, monitor[1]) + 50,
           min(r.right, monitor[2]) - 22, min(r.bottom, monitor[3]) - 60)   # unten Taskleiste frei lassen
# Sicherheitscheck: der Ausschnitt darf nur das Testfenster zeigen
pt = ctypes.wintypes.POINT
for px, py in [(bereich[0] + 3, bereich[1] + 3), (bereich[2] - 3, bereich[3] - 3),
               (bereich[0] + 3, bereich[3] - 3), (bereich[2] - 3, bereich[1] + 3)]:
    u32.WindowFromPoint.restype = ctypes.c_void_p
    oben = u32.GetAncestor(ctypes.c_void_p(u32.WindowFromPoint(pt(px, py))), 2)  # GA_ROOT
    if oben != hwnd:
        print(json.dumps({"aufgabe": aufgabe, "seed": seed,
                          "ergebnis": "ABGEBROCHEN: anderes Fenster im Testbereich"}))
        subprocess.run(["taskkill", "/f", "/t", "/pid", str(edge.pid)], capture_output=True)
        sys.exit(1)

# Einstellungen nur als Kopie (echte bleiben unveraendert), "ohne Nachfrage" an
tmp = os.path.join(tempfile.gettempdir(), "screenhelfer_stress_config.json")
shutil.copy(s.CONFIG_FILE, tmp)
s.CONFIG_FILE = tmp
s.App.starte_update_pruefung = lambda self, von_hand=False: None
app = s.App()
app.auto_schreiben.set(True)

# Fehlersuche: festhalten, wohin geklickt wird (Bild mit Markierungen in stresstest/debug/)
_orig = app._felder_eintragen
def _mit_protokoll(felder, l):
    from PIL import ImageDraw
    bild = s.ImageGrab.grab(bbox=(l["x"], l["y"], l["x"] + l["b"], l["y"] + l["h"]), all_screens=True)
    d = ImageDraw.Draw(bild)
    for f in felder:
        ymin, xmin, ymax, xmax = f.box
        d.rectangle([xmin * l["b"] / 1000, ymin * l["h"] / 1000, xmax * l["b"] / 1000, ymax * l["h"] / 1000],
                    outline="red", width=3)
        d.text((xmin * l["b"] / 1000, ymax * l["h"] / 1000 + 2), f"{f.name}={f.text}", fill="red")
    os.makedirs(os.path.join(HIER, "debug"), exist_ok=True)
    bild.save(os.path.join(HIER, "debug", f"{aufgabe}_s{seed}.png"))
    return _orig(felder, l)
app._felder_eintragen = _mit_protokoll
start = time.time()
log = {"aufgabe": aufgabe, "seed": seed}


def ziehen():
    vx, vy = app.v_off
    app.cv.event_generate("<ButtonPress-1>", x=bereich[0] - vx, y=bereich[1] - vy)
    app.cv.event_generate("<B1-Motion>", x=bereich[2] - vx, y=bereich[3] - vy)
    app.cv.event_generate("<ButtonRelease-1>", x=bereich[2] - vx, y=bereich[3] - vy)


ENDE = ("Rein", "Eingetragen", "Fehler", "Seite", "Keine", "Gratis", "API", "Fertig")
def warten(stabil=0):
    st = app.status.cget("text")
    if app.phase is None and st.startswith(ENDE):
        if stabil >= 8:                                  # 2 s lang unveraendert -> fertig
            log["status"] = st
            log["sekunden"] = round(time.time() - start)
            log["antwort"] = app.text.get("1.0", "end").strip()[:400]
            log["kontext_geholt"] = "vorherige" in " ".join(log.get("stati", []))
            log["ergebnis"] = titel(hwnd)
            if raender() != (r.left, r.top, r.right, r.bottom):
                log["ergebnis"] += "  [WARNUNG: Testfenster hat sich verschoben]"
            app.root.destroy()
            return
        app.root.after(250, lambda: warten(stabil + 1))
        return
    log.setdefault("stati", [])
    if not log["stati"] or log["stati"][-1] != st:
        log["stati"].append(st)
    if time.time() - start > 480:
        log["ergebnis"] = "ZEITUEBERSCHREITUNG: " + titel(hwnd)
        app.root.destroy()
        return
    app.root.after(250, warten)


app.root.after(800, app.starte)
app.root.after(2500, ziehen)
app.root.after(3500, warten)
app.run()
edge.terminate()
subprocess.run(["taskkill", "/f", "/t", "/pid", str(edge.pid)], capture_output=True)
os.remove(tmp)
print(json.dumps(log, ensure_ascii=False))
