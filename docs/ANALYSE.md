# Repository-Analyse: Yakoon

> Erstellt am 2026-06-04

## 1. Zweck der Anwendung

**Yakoon** (Yet Another Kernel for Ontological Networks) v0.4.0 ist ein **servergesteuertes, event-sourced UI-Runtime-System** in Python 3.11+. Es implementiert ein deklaratives Projektionsmodell nach dem SAM-Pattern (State-Action-Model). Der Kernel koordiniert Flows, verwaltet Zustand, steuert Blocking, delegiert Rendering und bleibt UI-agnostisch.

Die Kernidee: Ein "Flow" ist die Single Source of Truth. Projektion ist eine deterministische Funktion des Zustands, und der Zustand wird durch Event-Sourcing getrieben. Die Anwendung ist als **Text-UI- und Web-Terminal-Plattform** konzipiert – ähnlich einer Kommandozeile, aber mit strukturierten, reichhaltigen UI-Projektionen.

---

## 2. Architektur

### Schichtenarchitektur (Bottom-up)

```
y5ncore-base             (öffentliche API / Vertragsschicht, 0 deps)
  └─ y5nstore-event      (Event-Store, deps: y5ncore-base)
      └─ y5ncore-runtime (Engine, Scheduler, Projector, Compiler, Sessions, Auth)
          ├─ y5ntrans-ws (WebSocket-Transport)
          ├─ y5nspace-{shell,ident,runtime} (Plugin-Module)
          └─ y5napp-{console,web,ssh} (App-Einstiegspunkte)
```

### Datenfluss

```
Input (Tastatur/WebSocket) → InputParser → InputEvent
  → InvocationResolver (Baumdurchlauf) → CommandEngine
    → Scheduler (Queue) → Runner → Flow (Generator)
      → Outcome + Control + Effect
        → Projector (Jinja2 → AST → Projection)
          → EventDispatcher → Transport → Client
```

### Kernprinzipien (aus `docs/ARCH.md` und `docs/DECISIONS.md`)

- Der Kernel bleibt domain-neutral – Domänen entstehen durch Komposition
- Das Platform definiert Topologie, nicht Semantik – Plugins besitzen die Sprache
- **Stateless Engine, Stateful Execution (Generatoren)** – kein Semaphor, keine Tasks, kein Async-Event
- **Flow ist die Single Source of Truth** – Projektion ist deterministische Funktion des Zustands
- Capabilities werden an den Ort der Nutzung weitergereicht ("Fähigkeiten werden bis ans Ziel gereicht")

---

## 3. Hauptmodule

### 3.1 `y5ncore-base` (Grundschicht)

- **Node-System**: `y5n/base/nodes/node.py` (410 Zeilen) – `Node`, `NodeScope`, Hierarchie, Ports
- **Flow-Primitives**: `Outcome`, `Control` (Stop, Continue, AwaitEvent, Foreground, ...), `Effect` (EmitView, EmitEvent, ...)
- **Projektionsmodell**: Block-Typen (paragraph, heading, list, kv, stack, flow, section, ...), Inline-Typen (text, em, strong, code, link, cmd, arg, ...)
- **Projektionstransfer**: Serialisierung/Deserialisierung für das Drahtprotokoll
- **Policy-Framework**: `IntPolicy`, `StringPolicy`, `BoolPolicy`, `DatePolicy`, etc.
- **PerceptualStream**: Framebudget-gesteuertes Streaming mit Timing und Jitter
- **Transport-Abstraktion**: `Transport`, `IO`, `ports.py`
- **Ressourcensystem**: `ResourceRef`, `Resolver` für importlib-Ressourcen

### 3.2 `y5nstore-event` (Event-Store)

- **EntityStore**: 4D-Adressierung `(domain, kind, space, entity_id)`, z.B. `system/account/develop/123`
- **Current Table** (materialisierter Zustand) + **Revisions** (append-only Patches) + **Snapshots** (periodische Materialisierung)
- **Backends**: `MemoryBackend` (Dev/Test) und `PostgresBackend` (Produktion)
- **Patch-Strategien**: `JsonPatchStrategy`, `FastPatchStrategy`
- **Scan-Operationen**: Prefix, Range, Equality, Cursor-basiert
- **Snapshot-Richtlinien**: Auto, Commit, Never

### 3.3 `y5ncore-runtime` (Runtime-Kern)

- **Machine**: `engine.py`, `scheduler.py`, `runner.py`, `host.py`, `parser.py`, `resolver.py`, `queue.py`, `session.py`
- **Projector**: Jinja2-Template-Rendering → Compiler (Tokenizer → AST → Normalizer → Projection)
- **Projektions-Compiler**: Block-Mapper (~15 Typen), Inline-Mapper (~10 Typen), AST-Builder
- **Streaming**: `EventStreamOutput`, `ProjectionDispatcher`
- **Capabilities**: Discovery (Service-Registrierung), Workflow (Flow-Ausführungs-Engine), Permission (Rechteprüfung)
- **Session-Management**: Session-Lebenszyklus, Permission-Bindung
- **Naming**: Namensallokation, Zähler, Sharding
- **DataSources**: Runtime-Introspektion (`NodeSource`)
- **Settings**: BaseSettings, AISettings, StorageSettings, LoggingSettings

### 3.4 Spaces (Plugin-Module)

- **`y5nspace-shell`**: Shell-Root-Node, `system`-Kommando
- **`y5nspace-ident`**: Identität & Authentifizierung – `user`, `group`, `grant`, `membership`, `whoami`, `su`
- **`y5nspace-runtime`**: `welcome`, `version`, `labs`, `jobs` (bg, fg, list, stop)

### 3.5 Transporte

- **`y5ntrans-ws`**: WebSocket-Server/Client-Transport

### 3.6 Clients & Apps

- **`y5ncli-console` / `y5napp-console`**: PromptToolkit-basiertes Terminal-UI, Block/Inline-Renderer
- **`y5ncli-web` / `y5napp-web`**: FastAPI + uvicorn + vanilla JS Frontend (WebSocket-Client)
- **`y5napp-ssh`**: asyncssh-Server

---

## 4. Datenbankzugriffe

### Event-Store (`EntityStore`)

**Datei**: `stores/y5nstore-event/src/y5nstore/event/store.py` (728 Zeilen)

**Schlüsseloperationen:**

| Operation | Beschreibung |
|-----------|-------------|
| `append()` | Fügt ein Revision-Patch an, aktualisiert Current Table, schreibt Index-Terme, optional Snapshot |
| `replace()` | Vollständiger Dokumentaustausch (erzeugt intern ein Diff-Patch) |
| `get()` | Schnellpfad Current Table oder historisch via Snapshot+Replay |
| `get_many()` | Batch-Fetch |
| `scan()` | Cursor-basiertes Paginieren mit Equality/Range/Prefix-Scans |
| `gc()` | Garbage Collection basierend auf Aufbewahrungsrichtlinie |

### Backend-Implementierungen

**MemoryBackend** (`stores/.../backends/memory.py`):
- Dict-basiert mit `asyncio.Lock` für Transaktionssemantik
- Jeweils ein Dict für Current, Revisions, Snapshots, Index Terms

**PostgresBackend** (`stores/.../backends/postgres/postgres.py`):
- DSN via `StorageSettings.dsn` oder Umgebungsvariable `STORE_DSN`
- Standard: `postgresql://postgres:secret@localhost:5432/yakoon_dev`
- Tabellen: `current`, `revisions`, `snapshots`, `index_entries`
- Verwendet `asyncpg` für async PostgreSQL-Zugriff
- SQL-Queries sind parameterisiert (`$1..$N`), aber teilweise dynamisch mit String-Konkatenation gebaut (`index_scan`)

---

## 5. APIs

### Es gibt keine traditionellen REST-APIs – stattdessen ein Node-basierter semantischer Kommandobaum.

### Node-System (ersetzt Routing)

```python
@dataclass
class Node:
    key: str          # Kanonischer Name
    run: callable     # Coroutine-Generator-Handler
    setup: callable   # Setup-Handler
    scope: NodeScope  # NODE | GLOBAL | ROOT
    children: list    # Sub-Knoten (Sub-Kommandos)
    ports: NodePorts  # Capability-Ports (DI)
```

### Auflösungspipeline

1. **`InputParser.parse(text)`** → `InputEvent` (roher Input in strukturiertes Event)
2. **`InvocationResolver.resolve(tree, event)`** → durchläuft Knotenbaum, findet passenden Node, prüft Permissions
3. **`CommandEngine.dispatch(node, event)`** → erzeugt `Flow` (Node + Event + Cursor)
4. **`Scheduler.schedule_flow(flow)`** → reiht Flow in Ausführungswarteschlange ein
5. **`Runner.on_input(event)`** → leitet Input an Vordergrund-Flow oder dispatcht als neues Kommando

### Projektionspipeline (die "View"-Schicht)

1. **`Projector.project(resource_name, state)`** → lädt Jinja2-Template, rendert mit State-Kontext
2. **`Compiler.compile(text, context)`** → Tokenize → Build AST → Normalize AST → Build Projection
3. **`EventStreamOutput.send_projection(projection)`** → dispatcht Projektions-Events via `EventDispatcher`
4. Serialisierung als JSON → Transport → Client

### WebSocket-API (für Web-Clients)

- **Endpunkt**: `/ws`
- **Nachrichten**: Serialisierte `ProjectionEvent`-Objekte (JSON)
- **Kein Rate-Limiting implementiert**

---

## 6. Technische Schulden

### P0 – Kritisch (Produktion blockiert)

| Issue | Datei(en) | Beschreibung |
|-------|-----------|--------------|
| **Zyklische Abhängigkeit base→runtime** | `runtime/y5ncore-base/src/y5n/base/runtime/sessions/session.py:4` | `Session` importiert `PermissionSet` aus `y5n.runtime` – base kann nicht ohne runtime installiert werden |
| **Dead Import: `y5n.compose` fehlt** | `apps/y5napp-web/src/y5napp/web/runtime/runtime.py:1` | App stürzt beim Import ab |
| **Dead Import: `y5n.client` fehlt** | `apps/y5napp-ssh/src/y5napp/ssh/app.py:4-5` | App stürzt beim Import ab |
| **Ungenügender Passwortschutz** | `spaces/y5nspace-ident/src/y5nspace/ident/services/verifier.py:8-16` | Plaintext-Vergleich + unsalted SHA-256 |
| **SSH-Server ohne Auth** | `apps/y5napp-ssh/src/y5napp/ssh/app.py:54-55` | `return False` ("keine Auth nötig") |
| **Keine Tests** | gesamtes Repository | ~400 Python-Dateien, 0 Tests, kein Test-Runner konfiguriert |

### P1 – Hoch

| Issue | Datei(en) | Beschreibung |
|-------|-----------|--------------|
| **Falsche/Nicht deklarierte Abhängigkeiten** | 5+ `pyproject.toml`-Dateien | `y5nstore-event` deklariert `[]`, importiert aber `y5n.base`; `y5ncli-console` deklariert nur `y5ncore-base`, importiert aber `y5n.runtime` |
| **Duplikat-Verzeichnis `dsl copy/`** | `spaces/y5nspace-runtime/src/y5nspace/runtime/runtime/labs/dsl copy/` | Kopie von `dsl/receive.py` mit Leerzeichen im Pfad |
| **Harte Default-Credentials** | `stores/y5nstore-event/src/y5nstore/event/settings/storage.py:15` | Default-DSN: `postgresql://postgres:secret@localhost:5432/yakoon_dev` |
| **Demo-User mit trivialen Passwörtern** | `spaces/y5nspace-ident/src/y5nspace/ident/runtime/setup.py:230,239` | `password_hash="123"`, `password_hash="456"` |
| **God Class `EntityStore`** | `stores/y5nstore-event/src/y5nstore/event/store.py:1-728` | 728 Zeilen, 8+ Verantwortlichkeiten |
| **God Class `Node`** | `runtime/y5ncore-base/src/y5n/base/nodes/node.py:1-410` | 410 Zeilen, 6+ Verantwortlichkeiten |
| **Jinja2 autoescape=False** | `runtime/y5ncore-runtime/src/y5n/runtime/projection/rendering/engine.py:16` | SSTI-Risiko, wenn User-Daten in Template-Kontext gelangen |
| **Session-User auf `NO-USER!` gehärtet** | `runtime/y5ncore-runtime/src/y5n/runtime/runtime/sessions/session.py:236` | User-Resolution auskommentiert |
| **Debug default `True`** | `runtime/y5ncore-runtime/src/y5n/runtime/settings/base.py:10` | Debug-Modus standardmäßig aktiv |

### P2 – Mittel

| Issue | Datei(en) | Beschreibung |
|-------|-----------|--------------|
| **Broad `except Exception:`** | `scheduler.py:190,242`, `session_bus.py:47`, `machine.py:76`, `stream.py:59` | Fehler werden verschluckt ohne Logging/Handler |
| **SQL-String-Konkatenation** | `stores/y5nstore-event/src/y5nstore/event/backends/postgres/postgres.py:385-405` | Dynamische WHERE-Klauseln via String-Konkatenation |
| **Kein Rate-Limiting** | `transports/y5ntrans-ws/src/y5ntrans/websocket/server.py:45-55` | WebSocket-Eingaben ohne Limitierung |
| **Path-Traversal unzureichend** | `runtime/y5ncore-runtime/src/y5n/runtime/resources/reader.py:60-64` | `clean_rel()` entfernt absolute Pfade, aber nicht `..` |
| **Inkonsistentes Error-Handling** | diverse | `RuntimeError`, `ValueError`, `KeyError`, `DomainError` werden austauschbar verwendet |
| **`y5n.api`-Indirektion ohne Dokumentation** | `runtime/y5ncore-base/src/y5n/api/` | Reine Re-Exports ohne erklärten Zweck |
| **Namenskonflikt: `y5n.base.runtime`** | `runtime/y5ncore-base/src/y5n/base/runtime/` | Verwechslungsgefahr mit `y5n.runtime` |

### P3 – Niedrig

| Issue | Datei(en) | Beschreibung |
|-------|-----------|--------------|
| **`__old__/`-Verzeichnis** | `__old__/` | Sollte archiviert werden (Git-Tag/Branch) |
| **Kein Docker/CI-CD** | – | Auf Roadmap (v0.1) aber nicht umgesetzt |
| **`print()` statt `logging`** | `__old__/` | Legacy-print-Anweisungen |
| **Kein Lockfile** | – | Nur `requirements.txt` mit gepinnten Versionen, kein `poetry.lock` |
| **Ollama-URL default HTTP** | `runtime/y5ncore-runtime/src/y5n/runtime/settings/ai.py:7` | `http://localhost:11434` (akzeptabel für Dev) |

---

## 7. Verbesserungsvorschläge

### Kurzfristig (sofort umsetzbar)

1. **`dsl copy/`-Verzeichnis löschen** – unbeabsichtigtes Duplikat verursacht Import-Konfusion
2. **Fehlende Abhängigkeiten in `pyproject.toml` eintragen:**
   - `y5nstore-event` → `dependencies = ["y5ncore-base"]`
   - `y5ncli-console` → `dependencies = ["y5ncore-base", "y5ncore-runtime"]`
   - `y5napp-web` → `dependencies = ["y5ncore-base", "y5ncore-runtime"]`
3. **Dead Imports korrigieren** – `y5n.compose`, `y5n.client` ersetzen oder anlegen

### Mittelfristig

4. **Zyklische Abhängigkeit base→runtime auflösen** – `PermissionSet`-Protokoll oder Basis-Typ nach `y5n.base` verschieben
5. **EntityStore aufsplitten** – `ScanEngine`, `SnapshotManager`, `IndexManager` extrahieren
6. **Node entschlacken** – Hierarchie-Traversal in `NodeTree`/`NodeWalker` auslagern
7. **Passwort-Hashing auf bcrypt/argon2 umstellen** – Unsalted SHA-256 ist nicht sicher
8. **Test-Infrastruktur aufsetzen:**
   - `pytest`, `pytest-asyncio`, `pytest-cov` in `requirements.txt` aufnehmen
   - `pyproject.toml` mit `[tool.pytest.ini_options]` konfigurieren
   - CI/CD-Pipeline (z.B. GitHub Actions) für automatisierte Testausführung
9. **Jinja2 autoescape aktivieren** oder Output-Sanitisierung implementieren
10. **Broad `except Exception:` ersetzen** durch spezifische Exception-Typen plus Logging
11. **SQL-Query-Builder** für `index_scan` verwenden, String-Konkatenation vermeiden

### Langfristig

12. **Debug-Modus standardmäßig deaktivieren** – `debug: bool = False` in BaseSettings
13. **SSH-Authentifizierung implementieren** – Kombiniert mit hohem Risiko (port 8022 + "keine Auth nötig")
14. **WebSocket-Rate-Limiting** – Schutz vor Command-Flooding
15. **`__old__/` entfernen** – In Git-Tag `archive/pre-v0.4.0` auslagern
16. **Docker-Containerisierung** – Wie in ROADMAP.md vorgesehen
17. **Lockfile einführen** – `pip freeze > requirements.lock` für reproduzierbare Builds
18. **`y5n.api` klären** – Entweder dokumentieren (Public-API-Facade) oder entfernen
19. **Error-Handling-Richtlinie festlegen** – Einheitliche Exception-Hierarchie für Domain-Errors
