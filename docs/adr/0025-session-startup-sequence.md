# ADR 25: Session Startup Sequence

**Status:** Accepted — implemented

> **Startup determines execution and order. Structure determines
> authorization. Commands determine their own completion.**
>
> A newly created Runtime Session may begin with an ordered sequence of
> ordinary command invocations — the **Session Startup Sequence**. The
> sequence executes through the normal invocation path, grants no
> rights, bypasses nothing, and carries no authentication semantics.
> What runs is an installation decision; whether an item may run is
> Structure's decision, exactly as for any other invocation.

## Context

Today a newly created Runtime Session starts without any initial
invocation. In the standard installation this is visible as:

```
CREATE Session
    ↓
anonymous Session
    ↓
user invokes a protected command
    ↓
Access Denied
```

This behavior is authorization-correct. The problem is not missing
Guest access and not missing authentication enforcement. Yakoon already
has the required authorization semantics (ADR-15):

- `anonymous: true` — the capability may execute without permissions
  (the mechanism behind the public/utility nodes `su`, `logout`, `err`);
- otherwise — the normal permission authorization applies to the
  current Session's grants.

The behavior is proven in both directions: a `welcome` command without
`anonymous: true` correctly produces Access Denied for an anonymous
Session; once the flag is declared, the same command is invocable by
the anonymous Session through the normal authorization path. No
security semantics are missing.

What is missing is generic **initialization behavior for a newly
created Runtime Session** — independent of which Renderer is connected
and independent of authentication.

## Decision

Introduce the **Session Startup Sequence**: an ordered sequence of
ordinary Runtime command invocations executed when a **new Session is
created**.

```
CREATE Session
    ↓
Startup Sequence
    ├── command A
    ├── command B
    └── command C
    ↓
normal Session operation
```

A single startup command is simply a sequence of length one. Every
startup item is an ordinary invocation — nothing about it is special
except when it runs.

## Ownership

```
Distribution       may provide a default startup policy
    ↓
Installation       owns the effective startup policy
    ↓
Runtime            executes the startup sequence
    ↓
Renderer           only renders ordinary resulting output/interactions
```

Startup MUST NOT be owned by apps-shell. The behavior of the Runtime
Session must be independent of whether the client is the Shell, the
Console, the Web, or any future Renderer. For the user, Runtime startup
semantics must not change with the Renderer.

The effective startup declaration is installation/operator-owned and
must survive assemble/update (ADR-22). It therefore belongs under the
installation's `.yak/` state — the same layer that owns deployment
decisions ("what runs, and how", ADR-24) — not inside the materialized
`structure/`.

The declaration is `.yak/startup.yml`:

```yaml
startup:
  - welcome
  - mem
```

An ordered sequence of ordinary command strings. A missing file, an
empty document, a missing or empty `startup` key, or a non-sequence
value all declare no startup; invalid entries are skipped, not raised
(tolerant loading — an installation must not fail to boot over a
malformed declaration). The distribution seeding mechanism remains an
implementation decision, while the ownership rule is fixed:

- **Distribution** may provide a default.
- **Installation** owns the effective policy.

## Structure Is Not the Owner

Startup policy does not belong in `structure/.yak/yak.yml` or any other
materialized Structure metadata.

Structure describes nodes, capabilities, and their security semantics.
`anonymous: true` belongs to Structure because it describes whether
that capability may execute without permissions. Startup answers a
different question: **what should this installation execute when a new
Session is created?**

The materialized Structure is regenerable and managed (ADR-22) — the
wrong persistence boundary for operator policy. Operator edits inside
materialized Structure do not survive a pack changing the same file.
The root node metadata (`structure/.yak/yak.yml`) additionally describes
a node of the materialized filesystem, not installation policy
(ADR-23).

Packs must also not independently declare startup policy. That would
require precedence/merge semantics that do not exist, and would allow a
Pack to impose Session behavior on an Installation. A pack declares the
capabilities and dependencies it needs (ADR-18, ADR-19) — never the
session behavior of the installation that installs it.

## Authorization Invariant

This is a hard architectural invariant.

- Startup grants NO rights.
- Startup bypasses NO rights.
- Startup modifies NO permissions.
- Startup has NO authentication semantics.

Every startup invocation must use the ordinary Runtime invocation path:

```
startup item
    ↓
normal command dispatch
    ↓
parse / resolve
    ↓
validate
    ↓
authorize
    ↓
privileged gate
    ↓
execute
```

Existing Structure semantics remain authoritative. If a startup item
targets a node with `anonymous: true`, it may execute anonymously
exactly as today. Otherwise the current Session must possess the
required permission. A denied startup command must be denied through
the normal Runtime path. There is no startup-specific authorization
check and no bypass.

**Startup determines execution and order. Structure determines
authorization.**

## Authentication

Authentication is NOT part of the Startup architecture. `su` has no
special Startup status — it is an ordinary capability which MAY appear
in a startup sequence like any other command.

Conceptual examples (not a schema decision):

- `welcome` — the standard distribution's initial experience;
- `su` followed by `welcome` — an installation that wants an
  authentication-first flow;
- `/system/status` — an appliance's entry point;
- no startup sequence at all — an installation with pure manual entry.

The architecture must remain valid for:

- standard authenticated installations,
- partially public installations,
- completely anonymous installations,
- appliances and custom installations.

Not introduced: Guest, guest permissions, `requires_login`,
authenticated startup, authentication handshake state, special `su`
handling.

## Session Lifecycle

Startup is Session **initialization**. It is not client-connect
behavior, not renderer-connect behavior, and not re-authentication
behavior.

| Lifecycle event | Startup Sequence |
|-----------------|------------------|
| CREATE new Session | execute |
| same-process RESUME | do NOT execute |
| process-boundary RESUME | do NOT execute |
| additional client connection | do NOT execute |
| logout | do NOT execute |

Startup does not redefine connect/resume semantics. On CREATE, the
creating client is joined and subscribed **before** the startup
sequence begins, so ordinary startup output reaches that client through
the normal Session output path. Startup introduces no handshake
changes.

The fact that authentication is deliberately cleared on a
process-boundary resume does not redefine that resume as Session
creation. If re-entry behavior after process restart is ever required,
that is a separate architectural concern and must not bend Startup
semantics.

## Sequence Semantics

The Startup model supports an ordered sequence, not only a single entry
capability. Each item is an ordinary command invocation. Items execute
in declared order, and the next item must not begin before the previous
startup invocation/flow has completed — commands may be interactive or
asynchronous.

```
A
↓ completion
B
↓ completion
C
```

No new execution engine is introduced. The existing Runtime
Flow/Scheduler machinery is reused. Internally constructed events with
SCHEDULER origin enter the same `dispatch → resolve → authorize →
execute` path as client input (the start-command effect, the form
continuation) — startup items use exactly this ordinary dispatch.

For each item:

```
dispatch ordinary command
    ↓
no Flow materializes?
    ├── yes → advance to the next item
    └── no  → observe Flow completion
              → schedule Flow
              → wait for normal Stop
              → advance
```

**Startup serializes command completion, not command success.** A
command may remain active across cooperative interaction:

```
command
    → AwaitEvent
    → input
    → AwaitEvent
    → ...
    → Stop
```

Startup does not continue until that command's Flow reaches normal
Stop. The Command owns its domain semantics and decides when its own
Flow is complete; Startup knows neither whether a command
authenticates, retries, prompts, succeeds, fails, is interactive, nor
whether it is `su`. This is what allows a future interactive login
command to remain one invocation and one Flow across multiple
authentication attempts — without adding any interaction semantics to
Startup (the concrete `su` behavior is not designed here and remains a
`su` concern).

FORM interaction is NOT activated by this ADR.

## Flow Completion

Completion sequencing uses a generic Flow lifecycle primitive:
`Scheduler.when_complete(flow, session)`. The Scheduler owns the
definitive normal Stop transition, so it owns completion observation;
the primitive resolves exactly when that Flow reaches the Scheduler's
normal Stop lifecycle. Startup registers completion observation before
scheduling the Flow, then awaits it.

The architectural distinction is explicit:

**output destination ≠ completion notification**

Startup Flows carry no `out_channel` for completion. Output takes the
ordinary projection path; completion takes the Scheduler's generic
observation. There is no startup-specific completion bookkeeping, no
startup-specific `flow_complete` logic, no synthetic Startup Flow, and
no autostart Command.

## Failure Semantics

Startup introduces no error handling of its own. Each startup item uses
ordinary Runtime error semantics, and every ordinary command failure is
represented through the normal Runtime path (ADR-13: an error creates a
new invocation). The implemented boundary follows the dispatch
semantics of the command engine exactly:

1. **dispatch returns no Flow** — the invocation cannot execute
   (empty input, non-runnable node, failed error-node resolution). No
   Flow exists; nothing can be awaited. The sequence advances.

2. **dispatch produces an ordinary error Flow** — command not found,
   permission denied, invalid arguments, execution failure routed to
   the error node. This is a normal Runtime-visible command failure:
   the Flow is scheduled and awaited like any other, and the sequence
   advances at its normal Stop.

3. **an unexpected exception escapes dispatch** — a Runtime or
   infrastructure failure. Startup does not reinterpret it as "no
   Flow": the sequence aborts, and the failure is retrieved and
   reported by the detached startup task.

Therefore:

**Startup tolerates Command failures. Startup does not swallow Runtime
failures.**

No sequence-level failure state is invented: no continue/stop policy
switches, no retry, no startup result or status type. The engine's
per-invocation error isolation is the default.

## Renderer Independence

Startup output is ordinary Runtime output. Commands produce their
normal Documents/Interactions; Renderers render them normally. No
Renderer needs to know that an output originated from startup, and no
startup-specific rendering is introduced.

Startup does not capture, redirect, or re-emit output, and does not
change view mode or persistence semantics. Renderer behavior remains
ordinary Renderer behavior; Shell, Console, Web, and future clients
observe the same Runtime behavior.

## Non-Goals

Explicitly out of scope of this ADR:

- Guest access and guest permissions
- permission model changes
- `anonymous` semantics changes
- authentication redesign
- `ident.auth` changes
- `su` redesign
- FORM activation
- logout redesign
- Runtime Port architecture changes
- remote/federation work
- Shell-specific login UI
- handshake redesign
- replay/snapshot activation

Separate security concerns are deliberately NOT addressed here and must
not be smuggled in through Startup: validate-before-authorize ordering,
command/signature enumeration, the password verifier, rate limiting.

## Consequences

### Positive

- Startup behavior is consistent across Shell, Console, Web, and future
  clients — one policy per installation, not one per Renderer.
- Standard distributions can provide a useful initial experience without
  hard-coding authentication policy into a Renderer.
- Operators retain control over their Installation; the policy survives
  assemble/update.
- Public/anonymous installations remain fully supported — no Startup is
  a valid configuration, and nothing nudges toward login.
- Existing authorization remains the single source of truth.
- No special Runtime concept for login or Guest is introduced.
- Startup supports generic initialization beyond authentication
  (onboarding, appliance entry, session-scoped setup).

### Costs / trade-offs

- The Runtime gains a new Session lifecycle behavior.
- The Installation gains a startup-policy declaration with a new
  materialization boundary between distribution default and operator
  ownership.
- Ordered asynchronous/interacting commands require completion-aware
  sequencing on top of the existing Flow/Scheduler machinery
  (`Scheduler.when_complete`).
- Startup runs cooperatively outside `connect()` — an interactive
  startup command may hold its Flow open indefinitely while the
  creating client already operates the Session normally.

## Implementation

The accepted design is implemented as follows. These are consequences
of the architecture above — composition seams, not public API
contracts.

- `load_startup(...)` loads `.yak/startup.yml` at boot; the loaded
  tuple is carried on the RuntimeManager.
- `RuntimeManager.connect` identifies keyless connects as the only
  CREATE path (SessionBuilder keys are boot-unique, so a keyless
  connect cannot collide with a persisted session document).
- An internal `OnSessionCreated` composition hook fires **only** for
  CREATE, after the creating client has joined and subscribed.
- The machine wiring owns a private serial startup driver: ordinary
  dispatch (`Origin.SCHEDULER`), completion registration via
  `Scheduler.when_complete`, then scheduling. Startup execution runs
  cooperatively outside `connect()`, so connect never waits for an
  interactive startup sequence; the detached task retrieves and reports
  its own unexpected failures.
- Startup Flows receive no `out_channel`; their output follows the
  normal projection path to the joined client.

## Open Questions

Settled by the implementation and no longer open: filename and schema
(`.yak/startup.yml`), the Runtime hook (keyless CREATE in `connect`
plus the `OnSessionCreated` composition hook), CREATE-vs-resume
behavior, serial completion semantics (`Scheduler.when_complete`),
output routing (ordinary projection path, client joined before the hook
fires), and error continuation semantics (three-way boundary above).

Remaining open:

- distribution seeding implementation (how a distribution provides its
  default `.yak/startup.yml`)
- which startup commands the standard distribution ships — including
  whether `welcome` becomes `anonymous: true` in the pack source
- future interactive behavior of `su` (an explicit login mode would be
  a `su` concern, owned by `su` — not by Startup)
