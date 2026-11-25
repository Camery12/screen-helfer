"""Stresstest fuer den Screen-Helfer: alle Aufgaben-Typen mit mehreren Zufalls-Seeds.
Aufruf: py stresstest.py [seeds, z. B. 1,2]  [aufgaben, z. B. jahre,kontext]"""
import json, os, subprocess, sys, time

HIER = os.path.dirname(os.path.abspath(__file__))
AUFGABEN = ["gegeben", "faktor", "jahre", "kontrolle", "dreisatz", "mc", "rot", "zinssatz", "kontext"]
seeds = sys.argv[1].split(",") if len(sys.argv) > 1 else ["1", "2"]
auswahl = sys.argv[2].split(",") if len(sys.argv) > 2 else AUFGABEN

gesamt = bestanden = 0
for seed in seeds:
    for a in auswahl:
        out = subprocess.run([sys.executable, os.path.join(HIER, "eine_aufgabe.py"), a, seed],
                             capture_output=True, text=True, encoding="utf-8")
        try:
            r = json.loads(out.stdout.strip().splitlines()[-1])
        except Exception:
            r = {"aufgabe": a, "seed": seed, "ergebnis": "ABSTURZ: " + (out.stderr or out.stdout)[-300:]}
        ok = "ALLES RICHTIG" in r.get("ergebnis", "")
        gesamt += 1
        bestanden += ok
        print(("OK    " if ok else "FALSCH"), f"{a:10} s{seed}", f"{r.get('sekunden', '?')}s",
              "| kontext geholt" if r.get("kontext_geholt") else "", "|", r.get("ergebnis", ""), flush=True)
        if not ok:
            print("        status:", r.get("status"), "| antwort:", (r.get("antwort") or "")[:200].replace("\n", " "), flush=True)
        time.sleep(8)                                   # Gratis-Limit von Gemini schonen
print(f"\nERGEBNIS: {bestanden}/{gesamt} bestanden")
