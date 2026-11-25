# Stresstest fuer den Screen-Helfer

Ein Uebungs-Spielplatz mit schweren Aufgaben-Formularen (Zinsrechnung), an dem der
Screen-Helfer automatisch getestet wird.

- `stress.html` - die Testseite. `?t=<aufgabe>&s=<seed>` waehlt Aufgabe und Zahlen.
  Aufgaben: `gegeben`, `faktor`, `jahre`, `kontrolle`, `dreisatz`, `mc`, `rot`, `zinssatz`, `kontext`.
  Die Seite prueft selbst und schreibt das Ergebnis in den Fenstertitel
  (`STRESS ... ALLES RICHTIG` oder `FALSCH feld=wert(soll ...)`).
- `eine_aufgabe.py` - oeffnet eine Aufgabe in Edge und bedient den Screen-Helfer wie ein Nutzer.
- `stresstest.py` - laesst alle Aufgaben mit mehreren Zahlensaetzen laufen:
  `py stresstest.py 1,2,3` (Seeds) oder `py stresstest.py 1 dreisatz,kontext` (Auswahl).
- `fortschritt.py` - kleines Fenster mit Fortschrittsbalken.

Hinweise: braucht den Quellcode `screen_helfer.py` im Ordner darueber und einen Gemini-API-Key.
Waehrend des Tests nicht an Maus/Tastatur arbeiten. Pro Aufgabe 2-3 Gemini-Anfragen - das
kostenlose Tageslimit reicht fuer etwa einen kompletten Durchlauf.
