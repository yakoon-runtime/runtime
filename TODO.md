# TODO — Nächste Schritte

## Dringend (morgen)

- [ ] **Channel-Konzept** — fixer Channel `"os-result"` kollidiert bei parallelen
      Aufrufen. Jeder Flow braucht einen eigenen Channel.
- [ ] **receive-Timeouts entkoppeln** — nicht im Handler, aber der TaskRunner
      braucht einen Mechanismus, um hängende Prozesse abzubrechen (z. B. per
      `jobs stop`). Aktuell blockiert der Flow unendlich.
- [ ] **Weitere Domänen testen** — `os` ist der erste intelligente Node.
      Welche Fragen funktionieren noch nicht? Welche brechen den Loop ab?
- [ ] **MAX_STEPS = 10 evaluieren** — reicht das? Zu viel? Rate-Limit-Risiko?

## Mittel (diese Woche)

- [ ] **Retry-Logik in den Multi-Step-Loop einweben** — aktuell gibt es keinen
      Retry mehr. Wenn ein Kommando fehlschlägt, sieht die LLM den Fehler und
      entscheidet selbst. Das ist gut. Aber was, wenn die LLM aufgibt, obwohl
      ein Retry helfen würde?
- [ ] **LLM-Provider-Konfiguration ins Setup auslagern** — API-Key, Model,
      Base-URL sind hartcodiert in `setup.py`. Sollen die per Settings kommen?
- [ ] **Prompt-Versionierung** — der Prompt entwickelt sich schnell. Brauchen
      wir eine einfache Versionierung, um zu wissen, welcher Prompt zu welchem
      Verhalten geführt hat?

## Langfristig (Konzept)

- [ ] **Capabilities für Nicht-OS-Domänen** — Mail, CRM, ERP werden
      semantische Aktionen brauchen, nicht Shell-Kommandos.
- [ ] **Domain Context per Setup** — der Kontext (Benutzer, Home, CWD) wird
      aktuell im Handler ermittelt. Soll das ins Setup?
- [ ] **Shell als Port** — `start_task` ist ein Runtime-Mechanismus. Wenn wir
      Shell-Aufrufe als Port definieren, können Spaces ihn austauschen oder
      mocken.
- [ ] **Komposition** — `files = yield start_cmd("os", ...)` — was ist `files`?
      Ein String? Ein Objekt? Wie geben wir Daten zwischen Nodes weiter?
