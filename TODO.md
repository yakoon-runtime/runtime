# TODO — Nächste Schritte

## Heute besprechen

- [ ] **MAX_STEPS / Agent als Komponente** — der Multi-Step-Loop in `os.py`
      ist kein OS-Konzept mehr. Er ist ein generisches Agenten-Muster
      (State, Loop, Prompt, Beobachtung, Done/Error). Soll das eine eigene
      DSL-Komponente werden, analog zu `Form`?
- [ ] **receive / Timeouts** — kein OS-Problem, sondern Runtime. Scheduler,
      TaskRunner, Jobs. Müssen wir das heute vertiefen oder reicht das
      Bewusstsein?
- [ ] **Domänengrenze definieren** — `os` antwortet via `{"done": true}` auch
      ohne OS-Kommando (Witz, Kalenderwissen). Braucht der Node eine Regel
      wie "mindestens ein Kommando vor done"? Oder ist das harmlos?

## Warten kann

- [ ] **Channel-Konzept** — fixer Channel `"os-result"` kollidiert bei
      parallelen Aufrufen. Aber erst relevant wenn mehrere Flows gleichzeitig
      laufen. Infrastruktur, kein Erkenntnisgewinn.
- [ ] **Weitere Domänen testen** — zu früh. Erst verstehen, warum OS
      funktioniert, bevor mail/crm/calendar geöffnet werden.

## Mittel (diese Woche)

- [ ] **LLM-Provider-Konfiguration ins Setup auslagern** — API-Key, Model,
      Base-URL sind hartcodiert in `setup.py`. Sollen die per Settings kommen?
- [ ] **Prompt-Versionierung** — der Prompt entwickelt sich schnell. Brauchen
      wir eine einfache Versionierung, um zu wissen, welcher Prompt zu welchem
      Verhalten geführt hat?
- [ ] **Verschiedene Modelle testen** — Mistral Small, Qwen, Gemma, Llama.
      Verhalten vergleichen, bevor über LoRA nachgedacht wird.

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
