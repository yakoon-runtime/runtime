# Yakoon Architecture v0.7 — InteractionMode (Wizard + Form)

This document describes how Yakoon supports both **wizard-style prompts** and **form-based input** without compromising the core idea of a **text-first workflow engine**. It captures the current runtime model (queue + pump) and the minimal extensions needed for FormMode.

---

## 1. Goal

Yakoon remains a **text engine with workflows**, but clients may request different interaction styles:

- **WizardMode**: prompt-driven, line-based interaction (Console, current Kivy usage)
- **FormMode**: structured form input via **FormSpecs** (Kivy/Qt capable clients)

**Key constraint:** the engine must not describe UI design. It provides **semantic input requirements** only (fields, labels, constraints). The client renders.

---

## 2. Core Principle: No Command Returns — Pump + State

Commands **do not return structured results** for runtime control. Instead, Yakoon uses a single coherent control model:

- **Output** streams via `session.emit(...)`
- **Control flow** is driven by `CommandQueueService` (commands enqueue further commands)
- **Blocking for input** is represented by `DialogService` (waiting state)
- **Lifecycle** is represented via `Session` signals (e.g., `exit_app`)

This matches the existing runtime behavior and avoids introducing a second “truth channel” (e.g., `CommandResult`).

---

## 3. System Components and Responsibilities

### 3.1 Engine
- Executes `dispatch(session, input)`
- Runs commands
- Uses services (queue, dialog, workflow, projector)
- Emits output via `session.emit(...)`
- Has no UI knowledge

### 3.2 WorkflowService
- Starts workflows as **batches**
- Enqueues workflow steps as commands (`enqueue_next`)
- Maintains workflow/batch state (running, waiting input, completed, failed)

Workflow steps may:
- read/write dataset
- validate/transform/store
- or request input by setting DialogService waiting state

### 3.3 CommandQueueService
- Stores queued `DispatchInput` / commands
- Provides the next input (`next_input(session)`)
- Enables “run-until-blocked” by repeated dispatch while queue is drainable

### 3.4 DialogService (the blocking mechanism)
DialogService is the **official block state** that decides whether the runtime may keep pumping.

It provides:
- `is_waiting(session) -> bool`
- `get_mode(session) -> InteractionMode` (Wizard/Form)
- For Wizard: prompt-related mode (normal/secret) if applicable
- For Form: access to a stored **FormSpec / NeedInputSpec**
  - e.g., `get_form_spec(session) -> NeedInputSpec`

DialogService replaces command return values as the runtime’s “need input” signal.

### 3.5 Projector / Templates
Templates remain the primary tool for **text outputs**:

- confirmations, errors, lists, status
- wizard prompts (text questions)
- non-form informational content

In **FormMode**, prompts are replaced by **FormSpecs**; templates are not used for the input UI itself.

### 3.6 HostAdapter / Clients
Hosts are UI adapters. They do not “run” business logic; they:
- render prompts/forms
- collect user input
- submit input via a callback

ConsoleHost implements:
- `on_prompt(prompt, mode)`
- `on_ready(prompt)`

Form-capable hosts (Kivy/Qt/Web) additionally implement:
- `on_form(spec)`

---

## 4. Runner as the Runtime Kernel (“Pump”)

`Runner.drive()` is the operational state machine:

1. If `session.has_signal("exit_app")`: stop and call `host.on_exit()`
2. If `dialogs.is_waiting(session)`: stop pumping and ask the host to collect input
3. Otherwise: drain queued commands via `queue.next_input(session)` and `engine.dispatch(...)`
4. If the queue is empty: call `host.on_ready(...)` (or `on_idle()`)

This yields a deterministic “run-until-blocked” runtime without needing command return values.

---

## 5. InteractionMode: Wizard vs Form

### 5.1 WizardMode (prompt-driven)
- Workflow/commands set DialogService to “waiting (wizard)”
- Runner calls `host.on_prompt(prompt=..., mode=...)`
- Host collects a line of input and submits it
- Runner dispatches and continues pumping until blocked again or complete

### 5.2 FormMode (FormSpec-driven)
- Workflow/commands set DialogService to “waiting (form)” and store a **NeedInputSpec**
- Runner calls `host.on_form(spec=NeedInputSpec)`
- Host renders a form, collects structured values, submits them
- Engine continues the workflow; `validate`/`store` are internal steps

**Invariant:** the client must never jump to workflow steps (e.g., `validate`, `store`). The client only supplies values requested by the next expected input.

---

## 6. NeedInputSpec / FormSpec: Semantics, not UI

The engine provides:
- `field key` (e.g., `first_name`)
- `label` (e.g., “Vorname”)
- `kind/type`, `required`, `constraints`, `help` (optional)

The client decides:
- layout, widgets, styling
- grouping, tabs, responsiveness
- UX details (focus, spacing, etc.)

---

## 7. Consequences / Benefits

- One workflow, multiple renderers (Wizard/Form)
- No UI knowledge inside engine/commands
- Single coherent control model (queue + dialog state)
- Extensible to more modes (confirm, picklist, file upload) without redesign
- Debuggable via queue state + dialog state + emitted envelopes
- Hosts remain swappable (Console, Kivy, Qt, Web)

---

## 8. Minimal Required Extensions

1. Extend `DialogService` to store:
   - `InteractionMode` (WIZARD/FORM)
   - optional `NeedInputSpec` / FormSpec when in FormMode
2. Extend `HostAdapter` with optional `on_form(spec)`
3. Extend `Runner.drive()`:
   - if waiting:
     - WIZARD -> `on_prompt(...)`
     - FORM -> `on_form(spec=...)`

No further architecture changes are required.

---

## 9. Control Flow Diagram (ASCII)

```text
User Input
   |
   v
Runner.on_user_input(text)
   |
   v
engine.dispatch(session, DispatchInput(text))
   |
   v
Runner.drive()
   |
   +--> exit_app? ---------> host.on_exit() -> STOP
   |
   +--> dialogs.is_waiting?
   |        |
   |        +--> mode=WIZARD -> host.on_prompt(prompt) -> submit(text) -> back to dispatch
   |        |
   |        +--> mode=FORM   -> host.on_form(spec)     -> submit(values) -> back to dispatch
   |
   +--> queue.next_input?
   |        |
   |        +--> dispatch(next) -> continue pumping
   |
   +--> queue empty -> host.on_ready(prompt) / host.on_idle()
```

---

## 10. Non-Goals (guardrails)

- The engine does not emit layout instructions.
- Clients do not control workflow steps.
- No parallel control channel via command return values.
- Templates are for text outputs, not for describing forms.

---

End of document.
