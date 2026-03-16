## Reicht ein Commit-Kommentar – oder gehört das in DECISIONS.md?
> Faustregel: Wenn du es jemand anderem erklären müsstest → rein damit.
> Dokumentiert wird: Was? Und Warum?
---
> 1. S1: Pro Session genau ein aktiver Controller.
> 2. Orchestrierung: Engine orchestriert, Host entscheidet über Lifecycle (Signal).
> 3. Security: Permissions sind pro Command (rx), nicht über CommandSet-Gruppen.
--

## 26-03-16
**PerceptualStream - Verzicht auf Loop**
Der Stream arbeitet nur mit Step() und nicht mit Loop.
Wenn der Stream selbst eine Loop enthält (z. B. asyncio), 
wird er an eine Runtime gebunden und ist nicht mehr portabel.
Der PerceptualStream ist im Grunde ein Frame Scheduler und
ist eine deterministischen Render-Engine.

## 26-03-14
**ViewHeader & Dokument**
Der ViewHeader gehört nicht zum Dokumentinhalt, aber er gehört sehr wohl zur 
Präsentationsentscheidung des Hosts. Der Renderer sollte ihn nicht sehen – der Host schon. 
ViewHeader ist Host-Metadaten.

## 26-03-13
**Prompt_toolk**
Promptoolkit wurde eingeführt um aus der console eine richtige App zu bauen. 

## 26-03-14
**UI ist kein Screen**
UI ist ein Document, das wächst und sich verändert. 
So wir das festgelegt wurde, war klar, die Anwendung darf nicht mehr als Chatlog
arbeiten, sondern als Live-Runtime-Document.

## 26-03-12
**Einführung von LLM-Streaming**
Large Language Models Streaming wird nun nicht mehr nur durch den Server geregelt, 
sondern durch den PerceptionStream innerhalb des Outputs. 
Somit wird der ServerStreamer für den Transport angepasst und PerceptionStream für
die Art und Weise dar Ausgabe in Chunks. Derzeit unterstützt der Stream:
- Fragment Reconstruction (Transport-Entkopplung) rekonstruiert Text aus beliebig kleinen Fragmenten.
- Progressive Chunk Generation (Chunks werden dynamisch erzeugt)
- Frame-Budget Rendering - Rendering wird pro Frame begrenzt:
- Timing-Modell (Perceptual Timing) - simuliert natürliches Lesen.
  - Initial Delay - startet leicht verzögert, damit Text „erscheint“.
  - Frame Timing - begrenzt Render-FPS.
  - Jitter - zufällige Variation verhindert mechanisches Streaming.
  - Satzzeichen-Pausen - erzeugt ein sehr natürliches Lesen.
  - Lifecycle Control - führt  zu einem klaren Lebenszyklus.
    - Pause / Resume 
- Streaming Scheduler - kennt Producer & Consumer
  - buffers → produce → queue → render

## 26-03-10
**Streaming invariants**
- Struktur wird vor Text übertragen
- Text wird nur für veröffentlichte Nodes gesendet
- Chunkgröße wird geclamped
- Flush passiert maximal 30 FPS
- Jitter verhindert mechanisches Timing
- Punctuation erzeugt Lesepausen

## 26-03-08
**Neue Pipeline für UI**
Presenter
  → render state
  → normalize / merge blocks
  → hand block sequence to DefaultInputService
DefaultInputService
  → play blocks sequentially
  → stream or emit passive blocks
  → on fields(prompt): wait via DialogService
  → continue after result
  → accumulate PresentResult
Streamer
  → write exactly one block to the session

## 26-03-08
**Felder werden normale Blöcke**
Fields als normale Blocks → beseitigt die künstliche Input/Output-Trennung
InteractionService als Ablaufsteuerung → genau der richtige Ort für wait / validate / continue
Streamer auf Transport reduziert → Presenter bestimmt Struktur, Streamer überträgt nur

## 26-03-06
**Einführung von Capabilities vs. Fachlichkeit**
Plugins stellen nun nur noch fachliche Module und die Shell zur Verfügung.
Alle andere Fähigkeiten werden in Form von Capabilities innerhalb von Base 
und Platform abgebildet. Capabilitites bringen zum Teil Controller und 
Dienste mit und greifen auf den gleichen Registrierungs-Mechanismus wie
Plugins zurück.

## 26-03-05
**Einführung des Eventstores**
Einführung eines eigenen EventStores, Dieser basiert auf:
- Event-Sourcing light
- Snapshots
- Index-on-write
- cursor-basierter Pagination
- time-travel (as_of)
- Backends Memory und später Postgres
Entities werden eindeutig über vier Dimensionen adressiert:
- (domain, kind, space, entity_id) ==> z.B: system / account / develop / 123
Dabei werden folgende Tabellen verwendet:
- Current Table - Materialisierter aktueller Zustand -> (entity_id, rev, data, updated_at)
- Revisions - Append-only Änderungslog -> (entity_id, rev, ts, patch, patch_format)
- Snapshots - Periodische Materialisierung für schnellen Replay. -> (entity_id, rev, ts, data)
  Diese werden geschrieben: AUTO / COMMIT / NEVER
Patch Strategy System: 
- Patchstrategien sind austauschbar.
- Der Store speichert zusätzlich: patch_format
Scan API (Store) - der Store bietet:
- scan()
- Prefix wird im Store umgesetzt als:
  - lo = prefix
  - hi = prefix_end(prefix)
- Scans können zeitlich eingefroren werden:
  - scan(..., as_of=timestamp)
  - Damit entstehen stabile paginierte Scans über historische Zustände.

Zusammenfassung
Der EventStore unterstützt bereits:
- patch strategies
- snapshots
- revision log
- index-on-write
- prefix scans
- range scans
- equality scans
- cursor pagination
- freeze view (as_of)
- get_many batching
- MemoryBackend

## 26-02-27
**Streaming**
Die Architektur wurde von einer hybriden Rendering-Lösung (Snapshot + Streaming) 
auf ein reines **Streaming-First-Modell** umgestellt. Container-Blöcke (z. B. Listen, Key-Value-Paare) 
werden nun **rekursiv und einheitlich** gestreamt – ohne Duplikate oder Timing-Probleme. 
Renderer sind rein für die UI zuständig, während die Strukturlogik ausschließlich 
in der Streaming-Schicht liegt. Das Ergebnis: deterministisches Verhalten, klare Verantwortlichkeiten 
und Skalierbarkeit für zukünftige Blocktypen wie Tabellen oder Formulare. 
Die Umsetzung ist für `list` und `kv` abgeschlossen und validiert.

## 26-02-23
**input_mode wird fester Bestandteil von ViewFormDef**
input_mode: Literal["prompt", "form"] = "prompt"
Zwei Validierungsstrategien im InputService:
Der InputService delegiert abhängig vom input_mode:
**prompt**
- Feldweise Abfrage
- Sofortvalidierung pro Feld
- Kein Fortschreiten bei Fehler
**form**
- Batchvalidierung
- Fehler pro Feld
- Grundlage für zukünftigen FormBlock
**Hosts können:**
- dem Contract folgen (auto)
- Prompt-Modus erzwingen
- Form-Modus erzwingen

## 26-02-23
**Steaming in Output**
Die Platform unterstützt nun auch Streaming per Default. Der Host entscheidet dabei, 
indem er Streaming in der Session erlaubt oder ablehnt. Somit entseht ein interaktives
Gefühl beim Benutzer.

## 26-02-23
**GUI host & Eingabe lifecyle**
Eingaben (offene Prompts) werden durch ein immer quitiert. Somit können Hosts ihr Frontend 
entsprechend anpassen oder aufräumarbeiten erledigen. Dazu schickt die Platform 
an die Sessionausgabe ein: 
- `ViewSpec(kind="view", input=None, message=None)'`

## 26-02-22
**State-based Template Architecture**
Die bisherige Template-Struktur basierte auf:
- kind: command_view
- mehreren Sections (views, inputs)
- section_key Auswahl im Renderer
- YAML-first Parsing mit nachgelagerter Jinja-Verarbeitung
  - Diese war nicht möglich, sobald Jinja-Direktiven verwendet wurden.
Diese Struktur führte zu: 
- erhöhter Komplexität im Renderer, 
- mehrfach-Pfaden im ViewSpecService
- impliziten Zuständen innerhalb einer Datei
- unnötigen Sonderfällen vermischter Semantik zwischen View und State
Daher wurde entschieden, dass eine Datei genau einen Zuständ hält.
Vorteile:
- Dramatische Reduktion der Komplexität im Renderer
- Nur noch ein Parserpfad
- Keine Section-Magie
- Keine partielle YAML-Manipulation
- Keine Sonderfälle
- Zustände sind explizit im Filesystem sichtbar
- Caching wird trivial
- Testbarkeit steigt
- Architektur wird klarer und ehrlicher

kind: view
state:
  role: info
  title: ...
  blocks: [...]
  fields: [...]

## 2026-02-21
**Workflow als Plugin entkoppelt**
* WF-Commands (`wf.start`, `wf.input`, etc.) wurden aus der Shell entfernt.
* Workflow ist nun ein eigenständiges Modul/Plugin.
* Die Plattform kennt Workflow nicht mehr als Core-Bestandteil.
* Engine greift ausschließlich über definierte Ports (`WorkflowInternal`, Public Contracts) zu.
* WF kann optional geladen werden (Vorbereitung für NoWorkflow-Plugin).
Workflow ist jetzt ein Feature, kein Systemkern.

## 2026-02-21
**Plattform-Struktur neu geschnitten**
Projektstruktur getrennt:
* `platform` → Kern (Engine, Directories, Services, Policies)
* `exts` → Plattform-erweiternde Module (z.B. workflow, discovery)
* `apps` → Fachanwendungen (crm, office)
* `posts` → Infrastruktur-/Host-Integration
Apps sind jetzt:
* `crm`
* `office`

## 2026-02-21
**Discovery & Lookup eingeführt**
* Discovery-Strategie-Mechanismus implementiert.
* Lookup ersetzt festen Alias-Mechanismus vollständig.
* Alias & Tags sind jetzt:
  * Multilingual
  * YAML-basiert
  * Plugin-fähig
* Lookup läuft über `LookupResolverService`.
* Kein Lookup-Command-Roundtrip mehr notwendig.
* UI-Darstellung bei Mehrdeutigkeit über separates Command gelöst.

## 2026-02-21
**Command-Suche in CommandCatalogService ausgelagert**
Resolve-Logik vollständig aus `CommandDirectory` entfernt.
`CommandCatalogService` enthält nun:
  * `for_resolve_context(...)`
  * `for_controller(...)`
  * `for_controller_visible(...)`
  * `for_man_entries(...)`
* Scope-Regeln (CONTROLLER, SHELL, GLOBAL) sind zentralisiert.
* `CommandDirectory` materialisiert nur noch Commands.

## 2026-02-20
**Dispatch-System neu modelliert**
- Union statt Vererbung.
- Zwei explizite Transporttypen.
- Keine implizite Payload-Semantik.

## 2026-02-20
**TemplateSource / WorkflowSource**
TemplateSource und WorkflowSource wurden konzeptionell ersetzt.
Dazu wurde ein einziges ResourceReferences-Objekt pro Controller eingeführt.
Subpath wird nicht länger unterstützt. Dafür {lang} als placeholder.

## 2026-02-19
**Alias-Mechanismus**
Der Alias-Mechanismus wurde entfernt, der dieser im Code definiert wurde. 
Alias ist nun über Lookup multilanguagefähig.
Lookup wird über Discovery-Strategien gelöst.

## 2026-02-18
**WorkflowCompileService entkoppelt**
Der WorkflowCompileService übernimmt nun nur noch Parsing + Modellierung.
Dafür wurde der FileLoader eingeführt. Dieser übernimmt alle Dateizugriff im System.

## 2026-02-18
**CommandScope eingeführt**
- CommandScope ersetzt shell_builtins. Routing ist jetzt explizit und deklarativ.
- Visibility von Scope getrennt; Scope ist nicht Sichtbarkeit.

## 2026-02-17
**Umstellung auf ViewSpec**
Der Output-Stack wurde radikal vereinfacht. IO ist nun vollständig View-getrieben.
Die Architektur ist konsistent mit dem Input-/Workflow-Modell.
Die Runtime ist leichter verständlich und deutlich schlanker.
- OutputEvent wird vollständig entfernt.
- Es existiert nur noch ein IO-Einstiegspunkt: io.view(ViewSpec)
- Session.emit() akzeptiert ausschließlich ViewSpec.
- Keine Dict-Views mehr im IO-Pfad.
- Kein zweiter Kanal (err) mehr.
- role wird ausschließlich über OutputSpec.role bestimmt.
- op wird ausschließlich über ViewSpec.mode bestimmt.
- Transport-Parameter wie channel, region, meta werden entfernt.

## 2026-02-17
**Vollständige Integration der Workflows**
Die DSL arbeitet für Commands & Workflows übergreifend.
InputResult als saubere Datenkapselung (statt PromptResult)
InputView liefert view contracts für Ausgabe.

## 2026-02-16
**Weiterentwicklung der View- und Input-Architektur**
Dieser Schritt dient zur Vorbereitung deklarativer Workflows.
- inputs.<state>.fields wird als Liste von Field-Definitionen geführt.
- Jedes Feld benötigt ein verpflichtendes var (Zielvariable).
- Optional kann ein key als Alias definiert werden.
- prompt.ask() liefert ein PromptResult statt eines rohen dict.
- UI-spezifische Hinweise (z. B. secret) werden aus der policy abgeleitet und als ui-Metadaten bereitgestellt.
- Feldbasierte Flags wie secret werden nicht mehr direkt im Template gesetzt.
Eine DSL für Commands und Workflows: Beide verwenden nun identische Felddefinitionen.

## 2026-02-15
**Unified Input Model (FormSpec Only)**
* Auflösung der Trennung zwischen *Wizard* und *Form* im Kernel.
* Einführung eines einheitlichen Input-Vertrags über **FormSpec**.
* Ein einzelnes Prompt ist nun ein FormSpec mit genau einem Field.
* Entfernt:
  * `WAITING_WIZARD`
  * `wait_field()`
  * Prompt-basierte Workflow-Steps
* Neuer Workflow-Step: `input`
* `prompt`-Step vollständig entfernt.
* Host erhält immer eine Liste strukturierter Felder:
  * `key`
  * `label`
  * `hint`
  * `required`
  * `secret`
  * `options`
  * `default`
* UI entscheidet selbstständig über Rendering (Wizard-sequenziell oder echtes Formular).
Der Kernel ist vollständig UI-agnostisch. Dialoglogik und Darstellung sind sauber entkoppelt.

## 2026-02-14
**Einführung des Policy-Systems**
* Einführung eines zentralen `PolicyService`.
* Feldtyp, Validierung und Coercion werden über Policies definiert.
* Workflows und Presenter arbeiten nur noch mit Policy-Referenzen (z.B. `system:string`, `system:bool`).
* `system:bool` unterstützt flexible Eingaben (y/n, ja/nein, true/false, 1/0).
* Validierung ist vollständig aus Prompt-/Workflow-Code ausgelagert.
Input ist nun deklarativ typisiert und konsistent validiert.

## 2026-02-14
**Strukturierte Run-Definition**
* Einführung von `RunDef(key, args)`.
* `run` + `args` klar getrennt.
* Compiler-Regel:
  Wenn `args` gesetzt sind, darf `run` keine Whitespaces enthalten.
* DSL wird strikt validiert.
Workflow-Definition ist formaler, sicherer und weniger fehleranfällig.

## 2026-02-14
**Compiler-Refactoring**
Zerlegung des Workflow-Compilers in Builder:
  * `RunBuilder`
  * `InputBuilder`
  * `SwitchBuilder`
  * `StepAssembler`
  * `GraphValidator`
* Verbesserte Fehlermeldungen (`workflow:step` Präfix).
* YAML 1.2 Bool-Handling eingeführt (kein `on:` → `True` Bug mehr).

## 2026-02-14
**Projektweite Formatierung & Linting**
* Einführung von **Black** (Formatter).
* Einführung von **Ruff** (Linter).
* Entfernen inkonsistenter Formatierung.
* Frühzeitige Erkennung potenzieller Fehler.
Einheitlicher Code-Stil und höhere Wartbarkeit.

## [2026-02-10]
**Wenn ein Workflow darf nie mahr als der User**
Bedeutet: Privilege Escalation als Feature ist nicht erlaubt und bewart das System später vor den ganz teuren Security-Debatten bewahrt. Wenn ein Workflow mehr darf als der User, bedeutet das faktisch, ein komplettes Policy-System bauen (Run-as, Delegation, Approvals, Audit, Scope, Least-Privilege-Rollen, Secrets, Revocation)
- Workflows sind Orchestrierung, keine Berechtigungs-Abkürzung.

## [2026-02-09]
**Einführung Workflow & Kontexts (batch.values)**
Daten zwischen Commands werden nicht mehr implizit über Session-Zustand oder Command-Seiteneffekte weitergereicht, sondern explizit über einen Workflow-gebundenen Kontext (batch.values).
Begründung: Workflows dienen der Orchestrierung von Commands. Ein expliziter, pro Workflow isolierter Kontext macht Datenflüsse nachvollziehbar, testbar und unabhängig von der Ausführungsumgebung (CLI, Wizard, Form, Remote Host). Commands sind reine Operationen ohne implizite Abhängigkeiten. Workflows definieren sowohl Ablauf als auch Datenfluss. Named Arguments ermöglichen robuste Command-Aufrufe ohne Positionsabhängigkeit.

## [2026-02-06]
**Kivy-UI-Host**
Der UI-Kivy-Host orientiert sich an dem Terminal von Gnome und ist multishellfähig.

## [2026-02-06]
**Kiyy als Desktop-Technologien**
Kivy ist ereignis- und flussorientiert - nicht formularzentriert. Kivy lässt in Render-Logik denken, Qt zwingt UI-Logik zu verwalten. Zudem bleibt Kivy Python-first und ist OpenSource ohne Grauzonen in der Lizenz, die später teurer wird. Kivy steht unter der MIT-Lizenz. QT dagegen hätte dazu beführt, ein Framework zu bedienen. Yakoon lebt aber von:
- kontinuierlichen Outputs
- teilweisen Updates (Streaming)
- Zuständen, die sich im Fluss befinden
- Kivy zeichnet und kontrolliert den Render-Zyklus


## [2026-02-06]
**Desktop-Technologien als Frontend**
Für das Frontend wurden Desktoptechnologien gewählt. 
Desktop heißt: Kontrolle über den Rechner. Eine Desktop-App ist kein „Client“, sie ist ein Agent.
Yakoon könnte später ein verteiltes Command-Graph-System werden. "Commands auf allen Clients ausführen, die im Netzwerk verfügbar sind". Damit kann sie Dinge, die eine Web-Anwendung prinzipiell nicht kann:
- Prozesse starten & steuern
- Lokale Ressourcen orchestrieren
- Langlaufende Sessions halten
- Identitäten über Maschinen hinweg stabilisieren
- Netzwerke von innen heraus bilden

## [2026-02-05]
**DialogService**
Der globale DialogManager wurde aufgelöst, um den letzten globalen Zustand aus der Engine zu entfernen. Danach wurde er in einen 'DialogService' überführt, der nun über die ServiceFactory austauschbar ist.

## [2026-02-05]
**OutputAdapter**
Die Session kann Metadaten durch Commands nach an den IO-Adapter leiten. Somit kann ein Command der Außenwelt mitteilen, um welche Information es sich bei dem ausgegebenen Text handelt. Die Engine legt sich bei der Ausgabe nicht fest, sondern rendert nur entsprechende Templates.

## [2026-02-05]
**Service für Permission & Rollen**
Permissions und Rollen müssen dem System über einen Service zur Verfügung gestellt werden. Damit kann das gesamte Handling in der Platform verbleiben. Die Logik, wie Rechte und Rollen zusammenarbeiten, befindet sich ebenfalls in diesem Service.

## [2026-02-04]
**Batch & Workflow**
Durch die Einführung des 'DispatchInput' kann der Host vereinfacht werden. Somit nimmt nun auch die Engine keinen einfachen input:str mehr auf, sondern verwendet intern den DispatchInput. Dieses beinhaltet immer die Benutzereingabe + eine batch_id. Warum ist eine batch_id notwendig? Wenn innerhalb eines batches (Workflow) ein Fehler auftritt (z.B: PermissionDenied), dann dürfen die folgenden Commands (innerhalb der Workflow-Serie) nicht mehr ausgeführt werden. Durch die batch_id kann die Engine diese Commands nun ablehnen und aus der Queue entfernen. => On failure inside batch → cancel remaining batch items. Failure umfasst: PermissionDenied, CmdNotFound, ValueError, InternalError (je nach Policy)

## [2026-02-04]
**Permissions**
Permissions werden als Unix-Rechte umgesetzt: rx (read/execute). Das vorherige Konzept über Commandsets wurde aufgelöst, weil es nicht skalierfähig war. Nun kann für jedes Commmand ein Recht (rx) - (spter rx:rx) erteilt oder auch entzogen werden. Der Account unterstützt nun Rollen und Permissions. Beide werden durch das Command 'su' in die aktuelle Session geladen. Durch die Einführung des IdentityMapService, bleiben die kompilierten Berechtigungen übe die Sitzung in der Session enthalten.

## [2026-00-04]
**Hooks in Controller**
Die Hooks in Controllern wurden reduziert. Auch wurden alle Hooks aus dem Controller entfernt, die nur von der Shell genutzt wurden. Das System (Engine) macht nun zwischen Controllern keinen Unterschied mehr.

## [2026-02-04]
**IdentityMapService**
Das gesamte System braucht verlässliche Sessions über die Dauer einer Sitzung. Bisher wurde durch jeden Dispatch eine neue Session aus dem Store geladen. Das hatte zur Folge, dass jeder prompt eine neue Session angefordert hat. Im Code führe das dazu, das nach jedem Prompt die Session.runtime leer war. Durch die IdentityMap ist nun sichergestellt, dass Sessions erhalten bleiben.

## [2026-00-03]
**Domain-Models**
Domain-Models arbeiten nicht länger mit Vererbung. Stattdessen halten Domain-Models ihre Daten in einem internen Objekt (runtime/data) auf Basis von 'dataclass'. Auch damit Aufwand in PersistensLayer (Store) entsteht, ist es ehrlich. Denn dort gehört die Logik hin und nicht in Form eines Light-OR-Mappers ins Model.

## [2026-02-03]
**CmdQuit - Beenden des Hosts**
Um die Eventloop sauber zu beenden, wird in der Session ein Signal gesetzt. Den Host zu benenden ist Zumutung des Hosts und nicht der Engine. Daher darf die Engine den Abbruch der Loop nicht entscheiden -> Signal. Der Host reagiert nur darauf. Ein anderer Host kann somit entscheiden ob er sich beendet oder das Signal ablehnt. Wichtig: Signale dürfen nicht persistiert werden.

## [2026-02-03]
**Request trifft keine Entscheidung**
Das Request nimmt nur die Benutereingabe auf. Entscheidet aber selbst nicht, was Command und SubCommand ist. Das ist immer Aufgabe des einzelnen Commands, zu interpretieren, welcher Parameter was bedeutet.

## [2026-02-02]
**Workflow darf nicht selbst ausführen**
Loops oder Rekursion im WorkflowCommand = zweiter Scheduler = Fehlerquelle. Das würde dazu führen, dass der Prompt den Workflow unterbricht und die Kontrolle verliert. Daher kommt ein 'CommandQueueService' zum Einsatz. Dieser wird über die HostLoop abgearbeitet.

## [2026-02-02]
**Rename core Packages**
Alle Core-Module tragen im Modulename nun '-core-', um sich von den anderen Modules abzugrenzen. Core ist einzigartig, weil es:, nicht optional ist, keine UX hat, kein Plugin ist, und die Runtime überhaupt erst möglich macht. Das ist eine ontologische Sonderstellung. Alles andere – auch Shell, Auth, Office, CRM – sind Programme, also prinzipiell gleichartig. Somit gilt: _Nur Core bekommt ein technisches Präfix._

## [2026-02-01]
**Einführung eines WorkflowCommand**
Über das WorkflowCommand können Commands intern commands ausführen. Somit können workflows umgesetzt werden. Der Grund für die Implementierung ist die Verwendung von Shortcuts wie 'su'. Dieses Command wird auf der shell laufen, aber dort intern zu einem anderem Plugin routen über 'use auth; su <user>; exit'. Somit können beliebige Commands aus der Shell aufgerufen werden, ohne dass die Shell überfrachtet wird oder globale gültige Commands (doppelte Keys) notwendig werden.

## [2026-02-01]
**Shell hält die Hilfe**
Die Shell benötigt eine das Command 'man', welches das gesamte Hilfesystem darstellt. Auf Template-Ebene liegt die Hilfe immer in den Command-Templates in der Sektion 'man' des Command-Templates.

## [2026-01-31]
**Shell-Mode & Program-Mode**
Im Prompt des Hosts wird der aktuelle Mode angezeigt.

## [2026-01-30]
**Einführung einer Shell**
Bei den Überlegungen zur Architektur der zukünftigen Platform, ist der Gedanke gereift, sich an Unix/Linux anzulehnen. Dabei stellt die Platform das System und die Commandline die Shell dar. Die Shell unterstützt das Starten und Beenden von Programmen (Controllern). Dies geschieht über 'use'. Verlassen der Anwedungen über 'exit'. Die Platform darf somit nur noch Infrastuktur und Dienste bereitstellen. Alles andere muss von Anwendungen (Programs) unterstützt werden. Um die Abstraktion zu verfollständigen, wurde die 'shell' in ein eigenes package verschoben. 'yakoon.shell'. Die Shell unterstützt somit das "Starten" von Programmen über 'use' und befindet sie sich dann im ProgramMode.

## [2025-01-30]
**ServiceDirectory und 'protocol'**
Die ServiceDirectory wurde umgebaut, um mit 'type' statt 'str' als Schlüssel arbeiten zu können. Zudem werden nun typisierte Rückgaben geliefert. Konsumenten können nun 'protocol'-classes dazu nutzen Dienste an der ServiceDirectory zu registrieren und mittels 'protocol' abzurufen.

## [2025-01-30]
**Presenter ist nun Service**
Der 'Presenter' wurde zu einem Service umgebaut und ist nun in 'platform' und nicht länger im 'base' zu finden. 

## [2025-01-28]
**Template als Ressources nutzbar**
Durch die Einführung der Klasse 'TemplateSource', welche an Controllern deklariert wird, finden Command-Templates nun ihre Ressourcen in ihrem eigenem Modul. Somit wurde die Schuld, Templates bereitzustellen auf das Module (plugin) verschoben.

## [2025-01-28]
**Wiederaufname der Entwicklung**
Folgende Entscheidungen wurden getroffen: 
1. Web wird vorerst nicht weiter unterstützt, um die Platformentwicklung zu beschleunigen. Fokus liegt auf dem Kern der Anwendung.
2. Die Anwendung wird auf 4 eigenständige Module mit eigenem '.toml' aufgeteilt: 'base', 'platform', 'hosts' und 'compose'.
3. Abhängigkeiten werden nicht weiter über die Engine sondern über das Module 'compose' aufgelöst
4. Dienste werden genutzt, um Informationen innerhalb der Anwendung auszutauschen.
5. Dienste werden in die Platform verschoben und 'base' erhält Zugriff über die 'ServiceDirectory'. Dort legen die Dienste in Form von 'protocol'-files vor.
6. Das System wurde aufgeräumt und technische Schuld beglichen. 

## [2025-01-28]
**Wiederaufname der Entwicklung**
Nach langer Pause wird die Entwicklung wieder aufgenommen.

## [2025-06-09]
**Controller-basierte Modularisierung**
Wir behandeln jeden Systembestandteil (Mesh, Redis, Queue, Realm etc.) als eigenen Controller. Nur registrierte Controller sind verfügbar – nicht registrierte Features existieren für die Plattform nicht. Ein aktiver Controller kapselt seine Logik vollständig (inkl. Sub-Switch, Help, Dispatch). Das System bleibt damit modular, entkoppelt und dynamisch erweiterbar – ohne zentrale Routinglogik.

## [2025-06-07]
**Vergabeprozess für numerische IDs über Shards**
Beim Vergabeprozess für numerische IDs über Shards stellt sich die Frage, wann ein neuer Shard erzeugt werden muss. Ziel ist es, Ressourcen effizient zu nutzen und unnötige Ranges zu vermeiden. Ein neuer Shard wird nur erzeugt, wenn ein bestehender Shard entweder vollständig ausgeschöpft ist oder beim Speichern ein Konflikt (z.B. Parallelzugriff) auftritt.
Solange ein Shard noch Schreibkapazität hat und gespeichert werden kann, wird er weiterverwendet.
Vorteil: 
- minimale Anzahl von Shards
- saubere ID-Räume
- effiziente Nutzung der Datenbank
- keine unnötige Parallelisierung oder Leerlauf-Shards
Nachtrag: "Redis wurde bewusst vermieden – zugunsten eines nachvollziehbaren, speicherbasierten Shard-Counters.“

## [2025-06-06]
# Services dürfen andere Services konsumieren
Innerhalb der Domänenschicht ist es erlaubt, dass Services einander aufrufen und verwenden. Das ermöglicht saubere Kapselung von Logik und Wiederverwendung, ohne Layer-Grenzen zu verletzen. Ein Service darf jedoch keine Controller, IO-Schichten oder externe Systeme direkt verwenden – diese Verantwortung bleibt klar getrennt.

## [2025-06-06]
**Der SharedCounter liefert nur IDs, keine Keys**
Die Struktur eines Keys (domain, bucket, scope) ist domänenspezifisch und lebt im aktuellen Kontext – meist in der Session. Der CounterService hat keine Kenntnis darüber und liefert ausschließlich fortlaufende IDs. Services kombinieren diese ID gezielt mit bestehenden Kontextinformationen, z. B.: → `session.key.with_id(...)`
So bleibt die Verantwortung klar getrennt:
- Session = Kontext
- Service = Entscheidung
- Counter = technische ID-Vergabe

## [2025-06-06]
**Kein Leaken von Technik**
Infrastruktur-Komponenten wie der SharedCounterService, Row-Zugriff oder Key-Generierung dürfen ausschließlich im ServiceLayer verwendet werden. Weder Controller noch Engine sehen technische Hilfsmittel oder Detailzustände. Nur die Bedeutung („ein Raum wird erstellt“) darf durchgereicht werden – alles andere bleibt gekapselt.

## [2025-06-06]
**CounterService gerhört in interne Infrastruktur**
Der CounterService ist eine interne Infrastruktur – und wird ausschließlich durch die Domain-Services verwendet, niemals direkt durch Fassade, Controller oder Engine. Warum das richtig ist:
- IDs sind domänenspezifisch - Fassade kennt keine Objektdetails.
- Sie reicht Intention weiter, keine Strukturverantwortung - Kein Leaken von Technik	
- Counter bleibt reine Infrastruktur – kein globales Werkzeug - Erzwingt saubere Objekt-Konstruktion	
- Alles entsteht durch service.create(...), nie „halb von außen“

## [2025-06-06]
**Services sind für gültige Objekte verantwortlich**
Nur der jeweilige Service darf Objekte wie Session, Room oder Account in einen validen Zustand überführen. Das bedeutet: `.validate()` muss innerhalb des Services immer erfolgreich durchführbar sein. Weder Controller noch Engine dürfen IDs erzeugen, Felder ergänzen oder Validierung auslösen. Nur der Service kennt Kontext und Regeln – er trägt die alleinige Verantwortung. Somit erfolgt auch die Erzeugung gültiger Schlüssel über den Coutner-Service nur innerhalb der Services.

## [2025-06-06]
**Session.key darf niemals None sein**
Wir initialisieren jede Session mit einem vollständigen Key-Rahmen
(Domain, Bucket, Scope), aber lassen die ID bewusst leer (None).
Damit bleibt die Session eindeutig typisiert (z. B. "session/anon/live"),
aber erzeugt keine persistente ID, bis klar ist, dass sie gespeichert werden muss.
Ein `None`-Key wurde verworfen, weil:
- spätere Finalisierung unmöglich wäre (kein Kontext vorhanden)
- der Code zusätzliche Prüfungen auf `None` erfordert hätte
- Debugging, Logging und Namespacing unnötig erschwert würden
Stattdessen gilt: 
→ `session.key` ist **immer gesetzt**, aber `session.key.id` kann `None` sein.

## [2025-06-04]
**Services bauen Objekte, Stores liefern dicts**
Wir haben festgelegt, dass alle Stores ausschließlich mit dict arbeiten und keine Domainobjekte instanziieren.
Das Erzeugen, Validieren und Interpretieren von Objekten erfolgt ausschließlich im Service-Layer.
So bleibt der Speicher generisch, leicht austauschbar und testbar. Domainlogik gehört nicht in die Infrastruktur.
Das verhindert unnötige Duplikation und hält die Trennung klar.

## [2025-06-03]
**Setup-Funktionen & Registry-Struktur**
Jede Domain besitzt ein eigenes `setup.py`, das eine ServiceRegistry erzeugt.  
Die Stores werden über `create_store_registry()` zentral verwaltet und beim Setup übergeben.  
Alle Registry-Klassen sind explizit typisiert, enthalten aber keine Logik.  
Service- und Store-Registries sind getrennt, werden aber über `from_store_registry()` verbunden.

## [2025-06-02]
**003 – Kein ORM / Kein SQL-Mapper**
Wir verzichten bewusst auf ORMs wie SQLAlchemy oder Tortoise.  
Sie erzeugen versteckte Abhängigkeiten, Magie im Speicherzugriff und hohes Memory-Footprint.  
Stattdessen verwenden wir `asyncpg` + `PyPika` + explizite `StoreBase`-Klassen.  
Alle Datenzugriffe bleiben sichtbar, testbar und frei von Metaprogrammierung.

## [2025-06-01]
**StoreRegistry & ServiceRegistry**
Wir trennen Infrastruktur (StoreRegistry) von Anwendungslogik (ServiceRegistry).  
Jede Domain kapselt ihre eigene ServiceRegistry und bindet nur die Stores, die sie benötigt.  
Bootstrap entscheidet, welche Domains aktiv sind – nicht, wie sie intern aufgebaut sind.  
Das System bleibt testbar, erweiterbar und backend-agnostisch

## [2025-05-31]
**Kontextbasierte Architektur eingeführt**
Jede Domain besitzt ihre eigene ServiceRegistry, die alle Services kapselt (z. B. room, session, account).
Über einen ServiceRouter erfolgt die Auflösung pro Bucket.
Die Plattform kann so flexible, testbare und parallele Umgebungen betreiben.
Das System ist damit voll modular, multi-bucket-fähig und vorbereitet auf Persistenz, Testumgebungen und Paketinstallationen.

## [2025-05-30]
**Markdown bleibt als Importformat denkbar**
Markdown bleibt als Importformat denkbar – z. B. per Drag&Drop mit automatischer DB-Befüllung.

## [2025-05-30]
**Kein Markdown als Speicherformat**
Wir verwerfen Markdown als Speicherformat für Räume zugunsten einer SQL-basierten Lösung. Gründe: fehlende Zustandsfähigkeit, kein Multiuser-Support, keine Queries. Ziel ist eine skalierbare, persistente Welt mit dynamischer Erweiterbarkeit.

## [2025-05-29]
**Commands & Presenter**
Alle Commands verwenden das Presenter-System mit klarer template_key-Definition pro SaasCommand. Die Darstellung erfolgt vollständig über sprachfähige Jinja2-Templates, getrennt vom Code. Die Struktur verbessert Lesbarkeit, Mehrsprachigkeit und Konsistenz. Ausgabe-Logik ist vollständig kapselbar, testbar und flexibel. Der Presenter ersetzt direkte Ausgaben (session.emit, session.fail) durch eine semantische Schicht. Pfadangaben erfolgen explizit über get_template_path() – kein Hidden-Routing.

## [2025-05-29]
**Umgang mit KI (Intent Mapping)**
Entscheidung: Die KI fungiert ausschließlich als Berater zur Bedeutungserschließung von Benutzereingaben (Intent Mapping). Sie wählt mögliche Commands und Domains aus – führt aber nichts aus. Begründung: Die Plattform bleibt alleinige ausführende Instanz (Akteur). Die KI ist rein unterstützend (Berater) tätig. Damit wird verhindert, dass das Modell außerhalb der gültigen Systemlogik halluziniert – z. B. ungültige Commands erfindet oder nicht vorhandene Domains vorschlägt. Leitsatz: "Wer ist Akteur, wer ist Berater?" Nur die Plattform darf handeln. Die KI darf vorschlagen.

intent = ai_chat_prompt("Bring mich ins Ritterschloss")
if intent.is_valid():
    if session.auto_confirm and intent.command.safe:
        engine.dispatch(intent.to_command_string())  # z. B. "teleport #343"
    else:
        await ask(session, f"Willst du ausführen: {intent.command.key} {intent.command.args}?")

## [2025-05-29]
**Umgang mit KI (Intent Mapping)**
Entscheidung: Die KI wird nicht direkt zur Steuerung der Plattform genutzt, sondern dient ausschließlich der Interpretation von Benutzereingaben. Aus diesen ermittelt sie das passende SaasCommand, die zugehörige Domain und mögliche Argumente. Begründung: Die Plattform bleibt ausführende Instanz mit vollständiger Kontrolle. Die KI agiert als Intent-Resolver, nicht als Logikträger – das verhindert Automatisierungsfehler, Halluzinationen und wahrt Systemintegrität.

## [2025-05-29]
**Presenter**
Ein Presenter wurde eingeführt, um die gesamte Template-Struktur zu kapseln. Dieser Presenter arbeitet mit der Session ist so somit in der Lage direkt Templates an Clients zu versenden. Grund: Die Verwendung von Templates reduziert sich auf eine Erstellung des Presenters + pres.emit("key", **data). Zudem wurden die Prompts angebunden. pres.prompts.emit("key")

## [2025-05-28]
**Templates vs. Translater**
Entscheidung: Alle Benutzerausgaben werden über Jinja2-Templates pro SaasCommand und Sprache geregelt. Dies ermöglicht konsistente, übersetzbare Ausgaben mit klarer Struktur, einfacher Sprachumschaltung und vollständiger Trennung von Logik und Darstellung – ohne redundante Translator-Systeme.

## [2025-05-28]
**Memory Manager**
MemoryManager zur zyklischen Überwachung von Speicherveränderungen. Anzeige von Objekt-Trends mit Pfeilen und Delta-Werten. safe_input() ersetzt ainput() zur Vermeidung wachsender Closures. Keine Anzeichen für Memory-Leaks mehr bei Commands und Prompts.

## [2025-05-28]
**Timeout - offene Future**
Wenn der Aufrufer keinen Timeout setzt, wird automatisch ein Standardwert verwendet (z. B. 30 Sekunden). So wird jede Prompt-Blockade vermieden, auch wenn man’s vergiss

## [2025-05-27]
**Einführung IOAdpater**
Einführung eines `Output`, um Ausgaben (`out`, `err`) in einer gemeinsamen Struktur zu kapseln. Die Übergabe einzelner Callback-Funktionen wurde durch ein objektbasiertes Modell ersetzt, das klarer, testbarer und flexibler ist – insbesondere für Console, WebSocket und zukünftige Frontends. Der IO-Kontext wird nun konsistent per `Output` an Engine- und Session-Methoden übergeben.

## [2025-05-27]
**Prompt & Batch**
Clients, die kontinuierlich Requests verarbeiten (z. B. Console, Telnet, WebSocket), unterstützen interaktive Prompts (Benutzereingaben) während der SaasCommand-Ausführung. 
Diese Clients besitzen einen stabilen, zustandsbehafteten Kanal, über den Prompts korrekt empfangen und beantwortet werden können. Bei stateless Clients (z. B. REST-Services) kann hingegen nicht garantiert werden, dass ein gestarteter Prompt-Future überhaupt aufgelöst wird. Stateless-Clients dürfen keine interaktiven Prompts verwenden. Stattdessen müssen sie vollständige Abläufe als batch:-Kommandos ausführen, bei denen alle Eingaben im Voraus definiert sind. Daher: REST macht nur vollständige Abläufe und ist per Design zustandslos (auch wenn technisch machbar).

## [2025-05-27]
**Prompt-aware Batch Execution**
Introduce prompt-aware batch execution with internal input resolution. Reason: Avoid blocking the engine on ask() during batch processing while preserving execution order and prompt flow.

## [2025-05-26]
**Dynamische Commands per Domain-Hooks**
Zur Unterstützung kontextsensitiver Commands (z. B. Raum-Exits) führt jede Domain zwei Lifecycle-Hooks:
- on_before_resolve(session) → registriert dynamische Commands
- on_cleanup(session) → entfernt sie wieder
Dadurch wird dynamisches Routing pro Session möglich, ohne den Resolver oder die Registry zu verändern.Zudem werden nun Commands nur innerhalb eines Lifecycles angelegt und wieder entfernt.

## [2025-05-26]
**Festlegung von Ausführungsbedingungen für Commands**
Commands können festlegen, ob ein geladener Charakter erforderlich ist: requires_character = False
> Fehlt das Attribut oder ist es True, prüft der Domain-Hook on_before_run_command(...), ob session.data_runtime.character gesetzt ist – sonst wird die Ausführung blockiert.
> Damit steuert das SaasCommand selbst die Anforderungen an den Session-Zustand.n

## [2025-05-26]
**Klickbare Links**
Unterstützung von internen & externen Hyperlinks wurde wie folgt umgesetzt:
> externe Links -> markdown: [Open Docs](https://example.com)
> interne Links -> werden zu Commands: 
> [Show version](# "version"); [Show help version](# "help version")

## [2025-05-25]
**Session Data**
Wir unterscheiden zwischen RuntimeSessionData und StorageSessionData. RuntimeData nimmt ein Objekt auf, welches im Domain Hook für die Domain angehängt wird. Es enthält Daten wie Character oder Document. StorageSessionData beinhaltet die Daten welche durch den SessionService persistiert und geladen werden. Idee: Trennung der Daten zwischen Storage und Laufzeit.

## [2025-05-25]
**Template-Splitting**
Template-Splitting nach Format Jedes logische Template besteht aus drei eigenständigen Dateien: .md, .plain, .ansi. 
Je nach Client wird automatisch das passende Format gerendert.
> Der Versuch, ein einziges Template dynamisch umzuwandeln (per Policy oder String-Strip) führte wiederholt zu inkonsistenten Ausgaben, 
> erschwerter Wartung und unklarer Formatlogik. Die Trennung nach Format schafft Klarheit, bessere Testbarkeit und eine stabile Render-Pipeline.

## [2025-05-25]
**Template-Rendering mit Markdown**
Alle Ausgaben erfolgen über Jinja2-Templates mit Markdown-Syntax.
> Grund: maximale Flexibilität, anpassbares Layout (auch für Kundenlösungen), markdown-kompatibel (z. B. Webclient, Chat-Ausgabe); 
Struktur: gemeinsamer `templates/`-Ordner, unterteilt nach Domain (`templates/realm/`, `templates/system/`, etc.)
> Endung: .j2.md -> jinja2 + markdown -> (Syntax-Highlighting)
> Zeilenumbrüche: zwei Leerzeichen am Ende / dreifaches Backtick

## [2025-05-25]
**Yakoon als Lösungseinheit (Solution)**
Yakoon-Plattform ist nun nur noch Infrastruktur – Einstieg erfolgt über Solution/
> Architektur: Platform → Solution → Entry-Points (console, webapi, telnet, webclient)
> Jeder App-Start erfolgt über Solution/run_*.py
> Vorbereitung für: `yakoon init`, `yakoon dev`, `yakoon deploy --docker`

## [2025-05-24]
**Webclient mit React + Vite**
Yakoon-Weboberfläche läuft unter React (Vite + Tailwind).
> Vorteile: ultraschneller Dev-Cycle, modernes Build-System, Hot-Reload
> Styling: Dark-Mode, Markdown-kompatibel
> Start: `npm run dev` im webclient-Verzeichnis

## [2025-05-24]
**Versionierung über Git-Tags + Fallback-Datei**
Plattformversion wird über `git describe --tags` ermittelt; Fallback über `version.txt`.
> Bei Docker-Build: Version via `echo "..." > version.txt` setzen
> Annotated Git-Tags erforderlich: `git tag -a v0.3.1 -m "Yakoon version 0.3.1"`
