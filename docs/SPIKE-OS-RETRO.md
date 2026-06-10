# Spike Retrospective: y5nspace-os

> Erfahrungen aus dem ersten intelligenten Node (June 2026)

## Was wir gebaut haben

Ein OS-Space (`y5nspace-os`), der natürliche Sprache via LLM in
Shell-Kommandos übersetzt, gegen eine Blacklist prüft und ausführt:

```
User: "os zeige alle Prozesse"
  → LLM-Resolver: "ps aux"
  → Blacklist: ps ∉ BLACKLIST ✓
  → start_task("ps", args=["aux"])
  → receive() → out_text(stdout)
```

Technisch funktioniert der gesamte Pfad: Plugin-Registrierung,
LLM-Provider via Port, start_task/receive als Task-Kopplung,
Blacklist als Sicherheitsgrenze.

## Was nicht funktioniert

### 1. LLM halluziniert Shell-Syntax

Das LLM erfindet Flags (`lsusb --all`), verwendet ungültige
Kombinationen (`find` ohne Pfad), und generiert Shell-Konstrukte
(Pipes, Heredocs, Wildcards), die ohne Shell nicht interpretiert
werden können.

Beispiele aus der Praxis:

```
# LLM rät:
lsusb -A
# → invalid option

# LLM rät:
cat <<EOF
# → Heredoc ohne Shell nicht ausführbar

# LLM rät:
find -type f
# → "path must precede expression"
```

### 2. Domänenfremde Anfragen

Das LLM versucht, Anfragen außerhalb der OS-Domäne zu beantworten:

```
"schreibe Hello world auf russisch" → cat <<EOF (Übersetzung)
"öffne Mailclient" → thunderbird (GUI-Programm)
```

Das LLM hat keine natürliche Grenze zwischen "das kann das OS"
und "das sollte ein anderer Node machen".

### 3. receive ohne Timeout

`start_task` → `receive` blockiert unendlich, wenn der Task
fehlschlägt oder kein Event auf dem Channel landet.

## Konsequenz

Der Spike bestätigt die These aus `INTELLIGENT-NODES.md`:

**Shell-Kommandos sind der falsche Abstraktionsgrad für einen
KI-Resolver. Die KI muss semantische Aktionen wählen, keine
Shell-Syntax generieren.**

### Aktuelle Architektur (Spike)

```
LLM → roher Shell-String → shlex.split → create_subprocess_exec
```

- LLM muss Shell-Syntax beherrschen (tut es nicht zuverlässig)
- Jeder Fehler im Shell-String killt die Ausführung
- Sicherheit = Prompt + Blacklist (beides umgehbar)

### Ziel-Architektur (Intelligent Nodes)

```
LLM → Capability-Auswahl → Action Handler → Port
```

- LLM wählt aus einer Liste von Capabilities (`list_usb_devices`)
- Action Handler führt die korrekte Port-Implementierung aus
- Sicherheit = Capability-Registry + Permission-Hierarchie

## Nächste Richtung

### 1. Capabilities statt Shell-Commands

Der OS-Space definiert Capabilities:

```python
capabilities = {
    "list_processes":   {"run": ps_handler,     "doc": "Zeigt laufende Prozesse"},
    "list_usb_devices": {"run": lsusb_handler,  "doc": "Zeigt USB-Geräte"},
    "disk_usage":       {"run": df_handler,     "doc": "Zeigt Speicherbelegung"},
}
```

Der LLM bekommt nur diese Liste. Es antwortet mit einem Capability-Namen,
nicht mit rohem Shell-String.

### 2. Prompt-Struktur

```text
Verfügbare Aktionen:
  list_processes   – Zeigt laufende Prozesse
  list_usb_devices – Zeigt USB-Geräte
  disk_usage       – Zeigt Speicherbelegung

Antworte NUR mit dem Aktionsnamen.
```

Kein Shell-Wissen mehr nötig. Kein Halluzinieren von Flags.
Keine Syntax-Fehler.

### 3. Action Handler

```python
async def lsusb_handler(space, args):
    result = await space.ports.os.run("lsusb")
    yield out_text(result.stdout)
```

Der Handler kennt den korrekten Shell-Befehl.
Der LLM muss nur die richtige Aktion wählen.

### 4. Shell wird zum Port

```python
class OnRunCommand(Protocol):
    async def __call__(self, command: str, args: list[str]) -> CommandResult: ...
```

Der Shell-Aufruf wandert aus dem Handler in einen Port.
Der OS-Space stellt den Port bereit, Action Handler nutzen ihn.

## Offene Fragen

- Wer definiert die Capabilities? Space-Autor? Admin? User?
- Können Capabilities dynamisch erweitert werden?
- Wie sieht das Prompt für Capability-Auswahl aus (System-Prompt
  vs. Runtime-generiert)?
- Braucht jede Capability einen eigenen Handler, oder reicht eine
  Dispatch-Tabelle?
- Wie vermeiden wir, dass der Shell-Port selbst zur Sicherheitslücke
  wird (ein Action Handler könnte rm ausführen)?

## Zusammenfassung

Der Spike hat gezeigt: Das Pattern (LLM → Resolver → Blacklist → Port)
funktioniert technisch. Aber der Abstraktionsgrad "Shell-Kommando"
ist zu niedrig. Das LLM kann keine zuverlässige Shell-Syntax
generieren. Der nächste Schritt ist der Wechsel zu semantischen
Capabilities.
