"""Kleines Fenster mit Fortschrittsbalken fuer den laufenden Stresstest.
Aufruf: pyw fortschritt.py <ausgabe-datei> <anzahl-aufgaben>"""
import sys, time, tkinter as tk

datei, gesamt = sys.argv[1], int(sys.argv[2])
start = time.time()

r = tk.Tk()
r.title("Stresstest")
r.geometry("420x150+40+700")          # links unten, weit weg vom Testbereich rechts
r.attributes("-topmost", True)
r.configure(bg="#1e1e2e")
titel = tk.Label(r, text="Stresstest laeuft ...", bg="#1e1e2e", fg="#D97757", font=("Segoe UI", 12, "bold"))
titel.pack(pady=(10, 4))
cv = tk.Canvas(r, width=380, height=26, bg="#181825", highlightthickness=0)
cv.pack()
balken = cv.create_rectangle(0, 0, 0, 26, fill="#C15F3C", width=0)
prozent = cv.create_text(190, 13, text="0 %", fill="white", font=("Segoe UI", 10, "bold"))
info = tk.Label(r, text="", bg="#1e1e2e", fg="#cdd6f4", font=("Segoe UI", 10))
info.pack(pady=4)
letzte = tk.Label(r, text="", bg="#1e1e2e", fg="#7f849c", font=("Segoe UI", 8))
letzte.pack()


def aktualisieren():
    try:
        zeilen = open(datei, encoding="utf-8", errors="ignore").read().splitlines()
    except OSError:
        zeilen = []
    fertig = [z for z in zeilen if z.startswith(("OK", "FALSCH"))]
    ok = sum(z.startswith("OK") for z in fertig)
    n = len(fertig)
    cv.coords(balken, 0, 0, 380 * n / gesamt, 26)
    cv.itemconfigure(prozent, text=f"{round(100 * n / gesamt)} %   ({n}/{gesamt})")
    vergangen = time.time() - start
    rest = f" | noch ca. {round(vergangen / n * (gesamt - n) / 60)} min" if n else ""
    info.config(text=f"✔ {ok} richtig   ✘ {n - ok} falsch{rest}")
    if fertig:
        letzte.config(text="zuletzt: " + " ".join(fertig[-1].split()[:3]))
    if any(z.startswith("ERGEBNIS") for z in zeilen):
        titel.config(text="Stresstest fertig!", fg="#a6e3a1")
    else:
        r.after(2000, aktualisieren)


aktualisieren()
r.mainloop()
