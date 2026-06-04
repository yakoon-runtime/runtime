# Bewertung von Yakoon

## Eine ehrliche Einschätzung

---

## Was wirklich gut ist

### Generator-Flows

Ein Python-Generator, der zwischen Benutzereingaben pausiert – das ist kein Framework-Trick, das ist ein Sprachfeature als Architektur. Ich kenne kein anderes System, das das so konsequent durchzieht.

```python
async def run(space):
    name = yield receive()    # Stunden später fortsetzbar
    yield out(greet(name))
    # Lokaler State bleibt erhalten, kein Session-Overhead
```

Die meisten Systeme brauchen dafür State-Machines, Sagas, Workflow-Engines oder Session-Caches. Yakoon nutzt einfach `yield`.

### "Der Node-Baum ist die API. Für alle."

Dass Mensch, KI und Script denselben `InputEvent`-Pfad nehmen, ist selten so konsequent designed. Kein separater REST-Endpoint für Automation, kein spezieller Webhook für KI, kein extra SDK für Scripts. Ein Parser, ein Resolver, ein Scheduler.

```python
# Mensch:   "invoice list --status=open"
# KI:       invoice list --status=open
# Script:   invoice list --status=open
# → Dasselbe InputEvent, derselbe Node, derselbe Flow.
```

### Ports als Capability-System (provide↓ / publish↑)

Das ist mehr durchdacht als 90% der DI-Frameworks da draussen. Die wenigsten unterscheiden überhaupt zwischen "nach unten delegieren" und "nach oben exportieren".

```python
space.ports.provide(OnProject, my_project_fn)   # ↓ für Kinder
space.ports.publish(OnAuth, my_auth_fn)          # ↑ für Eltern
```

Kein globaler Container, kein Ambient-Authority-Grab. Sichtbarkeit ist an Baumposition gebunden.

### Bounded AI

"KI generiert Nodes, aber Nodes haben nur Ports" – das ist eine Antwort auf ein Problem, das die meisten erst in 2-3 Jahren haben werden. Während andere Systeme versuchen, KI-Output hinterher zu validieren, definiert Yakoon von vornherein, was KI *nicht* tun kann.

Die Architektur-Papers (`docs/PORTS.md`, `docs/OCAP-ANALYSE.md`, `docs/FLOWS-JOBS-SCHEDULER.md`, `docs/DETERMINISMUS.md`) sind die beste Codebase-Dokumentation, die ich je gesehen habe. Jemand hat hier sehr, sehr gut nachgedacht.

---

## Was nervt

### Keine Tests

Bei 400+ Python-Dateien und 11 Paketen gibt es **null Tests**. Kein pytest, kein Test-Runner, kein CI. Das ist kein "wir schreiben später Tests" – das ist ein Architekturrisiko.

Die Generator-Flows sind so zentral – eine Regression im `FlowCursor` oder `CommandEngine.step_flow` und niemand merkt's. Bis es in Produktion crasht.

### Dead Imports

```python
# apps/y5napp-web/.../runtime.py:1
from y5n.compose.demo_data import seed_demo_system_data  # Existiert nicht!

# apps/y5napp-ssh/.../app.py:4-5
from y5n.client.runtime import Client, create_runtime     # Existiert nicht!
from y5n.client.terminal import SSHTerminal               # Existiert nicht!
```

Die Web-App und SSH-App crashen beim Import. Das ist kein "Refactoring-Rückstand" – das ist **"seit Wochen kaputt und keiner hats gemerkt"**. Genau das, wovor Tests schützen.

### Sicherheitslücken

```python
# apps/y5napp-ssh/.../app.py:54-55
def begin_auth(self, username):
    return False  # keine Auth nötig
```

```python
# stores/.../settings/storage.py:15
"postgresql://postgres:secret@localhost:5432/yakoon_dev"
```

```python
# spaces/.../verifier.py:14-16
hashlib.sha256(secret.encode()).hexdigest()  # Unsalted SHA-256
```

SSH ohne Auth + harte Default-Credentials + unsalted Passwörter. Das sind keine "architektonischen Kompromisse" – das sind **Sicherheitslücken**.

Eine Architektur, die sich Gedanken über Capability-Security und OCAP-Prinzipien macht, darf solche Löcher nicht haben. Der Widerspruch zwischen `docs/OCAP-ANALYSE.md` (durchdacht) und den Live-Imports ist gross.

### Zyklische Abhängigkeit

```python
# runtime/y5ncore-base/src/y5n/base/runtime/sessions/session.py:4
from y5n.runtime.capabilities.permission import PermissionSet
```

Base importiert Runtime. Das ist ein Riss im Fundament. Wenn `y5ncore-base` nicht ohne `y5ncore-runtime` installierbar ist, ist die Schichtenarchitektur de facto ein Monolith.

---

## Fazit

Die **Architektur-Papers** sind die beste Codebase-Dokumentation, die ich je gesehen habe. Jemand hat hier sehr, sehr gut nachgedacht – über Capabilities, über deterministische Projektion, über KI-Boundedness, über Generator-basierte Flows.

Aber die **Code-Implementation** hat Lücken zwischen Denken und Tun.

| Bereich | Note | Begründung |
|---------|------|------------|
| Architektur-Konzept | 1+ | Generator-Flows, Ports, Node-Baum, Projection |
| Dokumentation | 1 | PORTS.md, OCAP-ANALYSE.md, FLOWS-JOBS-SCHEDULER.md |
| Tests | 6 | 0 Tests bei 400+ Dateien |
| Operational Security | 5 | SSH ohne Auth, unsalted SHA-256, Default-Passwörter |
| Dependency Management | 4 | Dead Imports, falsche pyproject.toml-Deklarationen |
| Schichten-Trennung | 3 | Zyklische Abhängigkeit base→runtime |
| KI-Vision | 1+ | Vorausschauend, durchdacht, dokumentiert |

Aktuell ist Yakoon ein **Proof-of-Concept mit Produktionsambitionen**, aber ohne Produktionsreife.

Wenn die Sicherheitslücken geschlossen, Tests geschrieben und die Dead Imports gefixt sind, ist Yakoon eines der interessantesten Systeme, die ich analysiert habe. Die Architektur ist besser als 90% dessen, was ich in Produktion gesehen habe. Die Implementation muss aufholen.
