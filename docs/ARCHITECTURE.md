# Yakoon Architecture

*Yakoon is a deterministic runtime for flows, state, and projections.*

## Core Philosophy

Traditional applications are built around user interfaces.

Yakoon is built around state.

**UI thinks in:**

* Buttons
* Screens
* Layouts

**Yakoon thinks in:**

* State
* Transitions
* Decisions

The user interface is not the source of truth.

The state is.

---

## Flow → State → Projection

A Flow is the source of truth.

A Projection is a deterministic representation of that state.

The user interface is a rendering of the projection.

```text
Flow
  ↓
State
  ↓
Projection
  ↓
UI
```

Meaning:

* **Flow** owns behaviour
* **State** captures decisions
* **Projector** is a pure function
* **Projection** is a materialized view
* **UI** is a client-side concern

The runtime never manipulates user interfaces directly.

There is no:

* show dialog
* open window
* render button

Only state transitions.

---

## Runtime Model

Yakoon consists of a small number of core concepts.

### Runtime

The runtime hosts flows, sessions and spaces.

### Session

A session represents a working context.

Sessions may outlive clients.

Multiple clients may attach to the same session.

Flows continue to run even when no user is connected.

### Flow

A flow is an executable state machine.

Flows produce outcomes and modify state.

### Projection

A projection is a deterministic representation of state.

Multiple clients can observe the same projection.

### Client

Clients render projections.

Examples:

* Texture
* Web
* Tauri

Clients never own state.

---

## Architecture Principles

### State First

State is the primary artifact.

User interfaces emerge from state.

### Deterministic Projection

The same state must always produce the same projection.

### Runtime Owns Context

Sessions, users, flows and state belong to the runtime.

Clients are transient.

### UI Agnostic

The runtime has no knowledge of Textual, HTML, browsers or desktop frameworks.

### Composition over Frameworks

Domains are added through spaces.

The runtime provides topology.

Spaces provide semantics.

---

## Kernel Analogy

Yakoon's runtime shares structural properties with an operating system kernel:

| Kernel Concept | Yakoon Equivalent |
|---|---|
| Process scheduler | Flow Queue |
| Process orchestration | Workflow Service |
| Blocking state (semaphore) | Dialog Service |
| Process context | Session |
| Device driver | Client Transport |
| System calls | Outcomes / Controls |
| Memory pages | Projections |

An OS kernel coordinates execution, manages state, controls blocking, and delegates presentation — all without knowing which applications the user runs.

Yakoon does the same for long-running flows: it schedules them, manages their state, blocks when input is needed, and delegates rendering to clients.

**The runtime is structurally closer to an operating system kernel than to a CRUD application.**

---

## Design Goal

Yakoon aims to make long-running work observable, resumable and independent of individual clients.

A flow may continue running:

* without an attached client
* across multiple clients
* across multiple sessions

The runtime remains the single source of truth.
