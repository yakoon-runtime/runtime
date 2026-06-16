# SAM — Event-driven state machine with deterministic projection
*SAM is a perceivable state machine*

## Core Philosophy

**UI vs SAM**
*UI thinks in:*
- Buttons
- Screens
- Layout
*SAM thinks in:*
- State
- Transitions
- Decisions

## The Flow

The Flow is the single source of truth. The Projection is a deterministic function of that state.
- UI does not exist — it emerges from state
- *Not:* "show button", "open dialog"
- *But:* "State is now this"

## Process & State & Projection

- Process determines State
- State determines Projection
- Projection determines UI

Meaning:
- **Flow** — State Machine
- **Projector** — Pure function: `projection = f(state)`
- **Projection** — Materialized view of the state

## Kernel Properties

What we are building has kernel characteristics:

| Kernel property | Runtime equivalent |
|---|---|
| Coordinates execution | Queue |
| Manages state | WorkflowService |
| Controls blocking | DialogService |
| Delegates presentation | Session |
| Remains UI-agnostic | Host |

This is structurally closer to an operating system kernel than to a CRUD app.

## Architecture Principles

- **Kernel remains domain-neutral**
- **Domains emerge through composition**
- **Platform defines topology, not semantics**
- **Plugins own language**
