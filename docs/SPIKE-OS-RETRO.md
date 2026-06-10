# Spike Retrospective: y5nspace-os

> Erfahrungen aus dem ersten intelligenten Node (June 2026)

## Was wir gebaut haben

Ein OS-Space (`y5nspace-os`), der natürliche Sprache via LLM in
Shell-Kommandos übersetzt, gegen eine Blacklist prüft und ausführt.

Drei Iterationen:

### V1: Raw Shell String

```
User: "os zeige alle Prozesse"
  → LLM: "ps aux"
  → shlex.split → start_task
```

**Problem:** LLM halluziniert Flags (`lsusb -A`), verwendet Heredocs
(`cat <<EOF`), vergisst Pfade (`find -type f`).

### V2: Restriktiver Prompt + Command-Whitelist

Prompt auf ~35 Kommandos eingeschränkt, Regeln für "keine Pipes,
keine Wildcards, kein sudo" verstärkt.

**Problem:** Leicht besser, aber Kernproblem bleibt — LLM generiert
weiterhin ungültige Shell-Syntax.

### V3: JSON Output Format (Lösung)

```
LLM → {"command": "ps", "args": ["aux"]} → json.loads → start_task
```

Prompt definiert ein striktes JSON-Schema:

```json
{"command": "<name>", "args": ["<arg1>", "<arg2>"]}
```

**Ergebnis:** Die Halluzinationen sind praktisch verschwunden.

## Die Erkenntnis

**Der Prompt war das Problem, nicht die Architektur.**

Die Fehler der V1/V2 waren kein Beleg dafür, dass Shell-Kommandos
der falsche Abstraktionsgrad sind. Sie waren ein Beleg dafür, dass
roher Shell-String der falsche Austauschformat ist.

Das JSON-Format zwingt das LLM in eine Struktur, in der es nicht
mehr raten kann:

- Kein `lsusb -A` — das LLM muss `args` als Liste explizit angeben
- Kein `cat <<EOF` — Heredocs passen nicht ins JSON-Schema
- Kein `find -type f` ohne Pfad — `args` macht fehlende Pfade sichtbar
- Domänenfremde Anfragen → `{"error": "..."}` statt kreativem Rateversuch

Der entscheidende Satz aus der Diskussion:

> Das LLM denkt in Shell. Die Runtime denkt nicht in Shell.
> Der Prompt muss diese Lücke schließen.

Der JSON-Zwang schließt diese Lücke.

## Was wir gelernt haben

### 1. Prompt-Engineering ist der Hebel

Nicht "LLM ist zu dumm für Shell", sondern "LLM braucht ein
Format, das es nicht zum Raten verleitet". Ein strukturiertes
Output-Format (JSON) wirkt besser als jede noch so detaillierte
Regel in natürlicher Sprache.

### 2. Blacklist + JSON-Schema = pragmatische Sicherheit

Die Blacklist verhindert destructive Kommandos. Das JSON-Schema
verhindert syntaktisch ungültige Kommandos.
Zusammen bilden sie eine ausreichende Sicherheitsgrenze für V1.

### 3. Capabilities sind nicht obsolet — aber später

Die ursprüngliche "Capabilities statt Shell" These ist nicht
widerlegt. Sie ist nur für den OS-Space noch nicht nötig.
Für Mail, CRM, ERP wird sie relevant — weil dort nicht
Shell-Syntax das Problem ist, sondern Geschäftslogik.

### 4. Das Prompt-Verhältnis

```
V1: Prompt weich, LLM frei      → viele Fehler
V2: Prompt streng, LLM frei     → weniger Fehler
V3: Prompt streng, Format fest  → kaum Fehler
```

## Offene Punkte

- **receive ohne Timeout** — wenn `start_task` fehlschlägt und kein
  Event auf dem Channel landet, blockiert der Flow unendlich.
  (Entschärfbar per `jobs stop`, aber kein Mechanismus im Handler.)
- **Channel-Konflikt** — fester Channel `"os-result"` kollidiert bei
  parallelen Aufrufen.
- **Fehlerbehandlung bei ungültigem JSON** — das LLM könnte
  trotzdem valides JSON mit falschem Command liefern
  (z. B. `{"command": "firefox"}` — dann greift die Blacklist).

## Ausblick

Der nächste Schritt ist nicht "Capabilities", sondern:

1. Channel-Konzept für parallele Aufrufe (pro Flow oder pro Session)
2. Timeout-Handling für `receive`
3. Weitere Domänen-Spaces nach dem gleichen Muster
   (`y5nspace-git`, `y5nspace-mail`)

Das JSON-Format bleibt als Pattern — jeder Space definiert sein
eigenes Prompt + Schema, die Blacklist bleibt die gemeinsame
Sicherheitsgrenze.

## Zusammenfassung

Das LLM braucht kein Shell-Wissen. Es braucht ein Format,
in dem es korrekt antworten kann. Das haben wir mit JSON
gefunden.
