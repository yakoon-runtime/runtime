**Drei Invarianten wie ein Prompt läuft:**
1. Ein Dispatch läuft, bis ein Prompt wartet oder der Command fertig ist.
2. Prompt-Antworten führen denselben Command weiter.
3. Nach jedem Dispatch gibt es genau einen Abschluss-Yield.


Was wir bauen, hat tatsächlich Kernel-Eigenschaften:

Ein Kernel:
- koordiniert Abläufe
- verwaltet Zustand
- kontrolliert Blockierung
- delegiert Darstellung
- bleibt selbst UI-agnostisch

Unsere Runtime macht exakt das:
- Queue = Scheduling
- WorkflowService = Prozess-Orchestrierung
- DialogService = Blocking-State
- Session = Kontext
- Host = Adapter

Das ist strukturell näher an einem Betriebssystemkern als an einer CRUD-App.

## Yakoon: Architektur für Wizard- und Form-Interaktion (v0.7 – InteractionMode)

### 1. Ziel

Yakoon bleibt eine **Textengine mit Workflows**, kann aber je nach Client **unterschiedliche Interaktionsarten** ausspielen:

* **WizardMode** (Prompt-Dialog, Console/Kivy heute)
* **FormMode** (FormSpec statt Prompt, z.B. Kivy/Qt später)

Die Engine beschreibt **nie UI-Design**. Sie liefert nur **Semantik** (Felder, Labels, Constraints). Der Client rendert.

---

### 2. Kernprinzip: Kein Command-Return, sondern Pump + State

Commands liefern **keine Rückgabewerte**.
Das System ist bereits korrekt als **Queue-/Pump-Runtime** gebaut:

* **Output** läuft als Stream über `session.emit(...)`
* **Control Flow** läuft über `CommandQueueService` (Commands enqueuen weitere Commands)
* **Blockierung auf Input** wird über `DialogService` modelliert (waiting/not waiting)
* **Lifecycle** via `Session signals` (z.B. `exit_app`)

Damit existiert bereits ein stabiler, deterministischer Steuerkanal – ein zusätzlicher `CommandResult` würde nur eine zweite Wahrheit einführen.

---

### 3. Hauptkomponenten und Verantwortungen

#### 3.1 Engine

* führt `dispatch(session, input)` aus
* kennt keine UI
* arbeitet Commands ab
* nutzt Services (Queue, Dialog, Workflow, Projector)
* emittet Output über `session.emit(...)`

#### 3.2 WorkflowService

* startet Workflows als **Batch**
* enqueued Workflow-Commands in die Queue (`enqueue_next`)
* pflegt Batch-/Workflow-State (running, waiting input, completed, failed)

Workflow-Steps sind normale Commands (oder workflow commands), die:

* Daten im Dataset lesen/schreiben
* validieren, transformieren, speichern
* *oder* Input anfordern (via DialogService)

#### 3.3 CommandQueueService

* hält eine Queue an `DispatchInput` (oder Commands)
* liefert das nächste Element (`next_input`)
* ermöglicht “run-until-blocked” durch wiederholtes Dispatching

#### 3.4 DialogService (entscheidender Blockade-Mechanismus)

DialogService ist der **offizielle Zustand**, ob die Engine weiter “pumpen” darf.

Er hält:

* `is_waiting(session)` → bool
* `get_mode(session)` → **InteractionMode** (Wizard/Form) + ggf. PromptMode (normal/secret)
* optional: `get_form_spec(session)` → FormSpec / NeedInputSpec

DialogService ersetzt Command-Returns als Steuermechanismus.

#### 3.5 Projector/Templates

Templates bleiben relevant für **Textausgaben**:

* Fehler, Bestätigungen, Listen, Hinweise
* Wizard-Prompts (Textfragen)

Im FormMode werden statt Prompt-Templates **FormSpecs** emittet. Templates werden dafür nicht gebraucht.

#### 3.6 HostAdapter / Clients

Der Host ist ein UI-Adapter, der **nicht** die Engine steuert, sondern nur:

* Input entgegennimmt
* UI rendert (Prompt oder Form)
* Input zurück an Runner submitten kann

ConsoleHost:

* implementiert `on_prompt`, `on_ready`

Form-fähige Hosts (Kivy/Qt):

* implementieren zusätzlich `on_form(spec=...)`

---

### 4. Runner als Runtime-Kernel („Pump“)

`Runner.drive()` ist die zentrale Laufzeitlogik:

1. Exit-Signal prüfen
2. Wenn Dialog wartet → Host auffordern Input zu sammeln (Wizard/Form) und **stoppen**
3. Sonst Queue drain: nächstes Input/Command holen, dispatchen, weiterpumpen
4. Wenn Queue leer → Host `on_ready`/`on_idle`

Damit ist „run-until-blocked“ bereits realisiert.

---

### 5. InteractionMode: Wizard vs Form

#### 5.1 WizardMode (Textprompt)

* Workflow/Commands setzen DialogService auf `WAITING_WIZARD` (oder `is_waiting=True`)
* Runner ruft `host.on_prompt(prompt, mode)` auf
* User liefert Text
* Runner ruft `engine.dispatch(...)` und pumpt weiter

#### 5.2 FormMode (FormSpec)

* Workflow/Commands setzen DialogService auf `WAITING_FORM` und speichern eine **FormSpec/NeedInputSpec**
* Runner ruft `host.on_form(spec)` auf
* User füllt Felder, Client sendet `submit(values)` (strukturiert oder serialisiert)
* Engine verarbeitet das als Input und pumpt den Workflow weiter
* validate/store sind interne Steps und werden **nicht vom Client angesteuert**

Wichtig: Der Client darf **niemals** „validate/store“ direkt triggern.
Er liefert nur Eingabe für den nächsten erwarteten Input.

---

### 6. FormSpec / NeedInputSpec (Semantik statt UI)

Engine liefert nur:

* `field key` (z.B. `first_name`)
* `label` (z.B. „Vorname“)
* Typ/required/constraints/help (optional)

Keine Layout-/Design-Information.

Der Client ist verantwortlich für:

* Layout, Widgets, Styling
* Interaktionsdetails (Tabs, Fokus, Grid, etc.)

---

### 7. Konsequenzen / Vorteile

* **Ein Workflow**, zwei Render-Weisen (Wizard/Form)
* Kein UI-Wissen in Engine/Commands
* Kein zweiter Steuerkanal (keine `CommandResult`)
* Erweiterbar: weitere InteractionModes (confirm, file, picklist) ohne Engine-Umbau
* Debuggbar: State liegt in Queue + DialogService + Session emits
* Host/Client bleibt austauschbar (Console, Kivy, Qt, Web)

---

### 8. Minimal nötige Erweiterungen

1. DialogService erweitert um:

   * `InteractionMode` (WIZARD/FORM)
   * optional gespeicherte `FormSpec`
2. HostAdapter erweitert um optional `on_form(spec)`
3. Runner.drive erweitert:

   * wenn `is_waiting`:

     * bei WIZARD → `on_prompt`
     * bei FORM → `on_form`

Alles andere bleibt unverändert.

---
