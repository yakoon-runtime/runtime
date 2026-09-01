# ADR 25: Session Startup Sequence

**Status:** Accepted — not yet implemented

> **Startup determines execution and order. Structure determines
> authorization.**
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

The exact filename and data schema are NOT frozen by this ADR. Working
names such as `.yak/session.yml` or `.yak/startup.yml` remain
implementation decisions. The distribution seeding mechanism is equally
an implementation detail, while the ownership rule is fixed:

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
Flow/Scheduler machinery is reused. The architecture already contains
runtime-initiated dispatch: internally constructed events with
SCHEDULER origin enter the same `dispatch → resolve → authorize →
execute` path as client input (the start-command effect, the form
continuation). Startup reuses this pattern; the concrete hook and
chaining mechanism remain implementation decisions.

FORM interaction is NOT activated by this ADR.

## Failure Semantics

Startup introduces no error handling of its own. Each startup item uses
ordinary Runtime error semantics — command not found, permission
denied, invalid arguments, execution failure — and every error is
represented through the normal Runtime output/error path (ADR-13: an
error creates a new invocation).

The continue-vs-stop behavior of a multi-item sequence is NOT an
architectural decision of this ADR. It is an open implementation
decision; no sequence-level failure state is invented. The engine's
per-invocation error isolation is the natural default.

## Renderer Independence

Startup output is ordinary Runtime output. Commands produce their
normal Documents/Interactions; Renderers render them normally. No
Renderer needs to know that an output originated from startup, and no
startup-specific rendering is introduced.

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
  sequencing on top of the existing Flow/Scheduler machinery.
- Startup output must be correctly ordered relative to Session/client
  readiness during implementation. The existing Session bus already
  delivers output to every subscribed client and drops output when none
  is subscribed; the concrete handshake-ordering guarantee remains an
  implementation decision and is not solved by this ADR.

## Open Implementation Decisions

These remain open and do not weaken any decision above:

- exact installation filename and data schema
- distribution seeding implementation
- exact Runtime hook/seam
- continue-vs-stop after a failed startup item
- output/handshake ordering implementation
- which startup commands the standard distribution ships
- whether `welcome` becomes `anonymous: true` in the pack source
- future interactive behavior of `su`
