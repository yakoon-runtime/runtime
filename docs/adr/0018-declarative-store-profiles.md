# ADR 18: Declarative Store Profiles

**Status: Validated**

The experiment's hypothesis — *can a pack declaratively describe its
persistence without knowing infrastructure?* — is proven end to end. The
model holds from the pack declaration to the resolver with no special
cases: `stores:` → parser → node → `BuildState` (inheritance) → tree →
`StoreCollector` → `StoreResolver` → `sdk.store("crm")`. No backend, DSN,
host, or password appears anywhere in the chain. The three packs (crm,
luma, ident) run on the new contract; an architecture test proves the full
path.

> **The pack describes what it needs. The platform decides how that need
> is met.**
>
> A pack declares the **logical stores it uses** — `stores: [crm]` — and
> nothing else. A store is a runtime service the pack's commands work
> against; a command is application logic and may orchestrate several. The
> `yak` tool translates the need into deployment configuration; the
> runtime resolves `sdk.store("crm")` to the declared store; the code never
> knows infrastructure.

## Key sentence

> **A pack declares the logical stores it uses, never infrastructure.**
> `stores: [crm]` says *"my commands work against the store called crm"* —
> which backend that is, where it lives, how it is tuned, is the
> deployment's decision. The code names a store the pack declared:
> `crm = sdk.store("crm")`.
>
> **A declaration names a capability; it never selects an implementation.**

The second sentence is the general form of the first — and of the whole
Yakoon line of capability declarations: `host`, `resources`, `entry`, and
now `stores` each name a capability, and none of them selects an
implementation.

## Vocabulary

> **Store profile** — what a pack declares about its persistence: the
> logical names it works against (`crm`, `security`, `telemetry`). A
> profile is a *need*, not a *specification*: it names stores, it never
> configures one.

> **Logical name** — the identifier the pack, the `yak` tool, and the
> deployment share. The deployment maps it to a physical store; the pack
> never sees the mapping. A logical name is pack knowledge, not
> infrastructure — like `ports.get("crm.contact")`, the code may name the
> store it works against.

> **Deployment** — the configuration that decides *how* a declared need is
> fulfilled: which backend, which DSN, which retention. It is the only
> place in the system that knows infrastructure.

The declaration is a sibling of the other pack-level needs, and it is as
minimal as they are:

```
host: python        → which interpreter runs my nodes
entry:              → which files are my entry points
resources:          → which assets I ship
stores: [crm]       → which stores my commands work against
```

Four needs, four names. None of them says *how*.

## Context

### Today there is one store, and packs are implicit

The runtime exposes a single store behind `sdk.store()`; every pack shares
it. There is no declaration — a pack simply calls `sdk.store()` and the
runtime answers. That worked while "the store" was unambiguous.

### ADR-17 already splits the history into two owners

ADR-17 fixed that Domain Events *are* the store's revisions and Activity
Events belong to the runtime — and that `events` is a projection over both,
not a subsystem. The projection's job becomes interesting only when there is
more than one place to project from. The store declaration is the step that
makes "more than one store" representable at all.

### The pattern already exists for entry, resources, and host

The platform has spent months removing infrastructure knowledge from packs
for the capabilities that came first. `entry:`, `resources:`, and `host:`
each follow the same shape: the pack names a need, the platform resolves
the instance. Persistence is the last major capability that still reaches
into the code (`sdk.store()` → runtime global) without a declaration in
between.

## Problem

1. **The pack has no way to say which store it needs.** "The store" is
   implicit; the moment there are several, `sdk.store()` is ambiguous.
2. **Describing infrastructure in the pack breaks the ownership chain.**
   A `store.profile` with backend, connection, or retention in `yak.yml`
   puts deployment knowledge where the pack declares — the exact split the
   platform has already won for `host`, `resources`, and `entry`.
3. **The runtime cannot bind before it knows the name.** Resolution
   (`sdk.store()`) needs a declared profile to bind against; otherwise the
   pack silently depends on deployment luck.
4. **The pattern is about to repeat.** Cache, messaging, scheduling, and
   other runtime services will face the same question. Without a stated
   principle, each will be decided ad hoc.

## Decision

### 1. A pack declares `stores:` — the logical stores it works against

`yak.yml` gains one top-level key:

```yaml
stores:
  - crm
```

Meaning: *this pack works against the store logically named `crm`.* A
single store is one entry; several stores are several entries — the format
never changes:

```yaml
stores:
  - crm
  - telemetry
```

That is the entire contract: the list of logical names the pack's commands
use. No nested object, no backend, no connection, no retention.

### 2. The pack knows only the names

The pack declares the stores' **logical names** and nothing else — not the
backend, not the instance. It does not even say whether a store is
postgres, sqlite, or memory:

```yaml
# never
stores:
  - name: crm
    backend: postgres
    host: db.company.local
    port: 5432
    database: crm
    username: stefan
    connection: postgres://...
    retention: 30d
```

The backend is *also* a realization, not a need — ``stores: [crm]`` says "I
need the store called crm", and it is the deployment's decision whether
that is a postgres cluster, a sqlite file on a Raspberry Pi, or a managed
database in a Kubernetes cluster. The pack describes its need; the
deployment describes the store (see *Four Layers of Store Knowledge*).

### 3. The code says `sdk.store()` or `sdk.store(name)`

A logical store name is not infrastructure — it is pack knowledge, exactly
like `ports.get("crm.contact")`. The code may therefore name the store:

```python
from y5n.sdk import store

crm = store("crm")              # the store called crm
telemetry = store("telemetry")  # another store the pack declared
```

`sdk.store()` without a name is a convenience for the common case of a
single declared store:

- exactly one store declared → that store;
- several stores declared → error: *"Multiple stores declared. Please
  specify a store name."*

Ambiguity is surfaced, never hidden behind a default.

### 4. The `yak` tool translates need into deployment

`yak install` reads `stores: [crm, telemetry]`, and asks for each: *"Store
'crm' — which backend?"* (postgres, sqlite, memory). If the store already
exists in the deployment configuration → does nothing; if it does not exist
→ asks the backend and instance, then adds it:

```yaml
stores:
  crm:
    backend: postgres
```

The pack never names a backend — the tool collects the logical store names
all installed packs declare, and the deployment decides what each name
means. The runtime starts with a deployment that knows `crm`, and
`sdk.store()` returns the store called `crm`.

The `yak` tool is not an installer of files — it is the **assembler of a
runtime environment**. A pack declares its needs; the tool collects the
needs of all installed packs and materializes the deployment that satisfies
them. Installing three packs (`crm` → `stores: [crm]`, `ident` → `stores:
[security]`, `telemetry` → `stores: [telemetry]`) yields three logical
stores in the deployment — and only then does the tool decide which already
exist, which to create, which to migrate. The store is the first capability
this mechanism serves; hosts, caches, queues, and schedulers follow the same
path. The pack never creates a database, opens a connection, or runs a
migration — it says "I use this logical store", and the platform builds it.

### 5. Ownership

| Level | Responsibility |
|-------|----------------|
| **Pack** | declares the logical stores it uses |
| **yak** | assembles the deployment from all installed packs' needs |
| **Runtime** | provides the store service |
| **SDK** | delivers `sdk.store(name)` |

### 6. Backward compatibility: a pack without `stores:` uses the default

A pack that declares no store keeps working — it binds to the default store
(today, the only one). The declaration is additive: `stores: [crm]` names
the store, no `stores:` means "the default". A single-store deployment is
simply the degenerate case where every logical name maps to the same
physical store.

## The General Principle

This ADR is not (only) about stores. It records a Yakoon principle that has
now accumulated four instances:

| Capability | Declaration |
|------------|-------------|
| Entry      | `entry:`    |
| Resources  | `resources:` |
| Host       | `host:`     |
| Store      | `store:`    |

All four follow the same shape:

> **A pack describes what it needs. The platform decides how that need is
> met.**

The pack is the place of *needs*; the deployment is the place of
*realization*; the code is the place of *neither*. This is the ownership
chain in its general form:

```
Pack declares → Tool prepares → Runtime resolves → Code stays clean
```

Store is the fourth capability to adopt it — not the last. Cache,
messaging, scheduling, and any future runtime service will meet the same
question: *what is the pack's need, and who decides the realization?* The
answer is already fixed here: **the pack declares the need; the platform
decides the how.**

## Language Independence

The store is not built for Python — it is built for Yakoon. The declaration
must therefore not be bound to any host language. Store profiles are part
of the component description (`yak.yml`), not part of a language SDK.

> **Store profiles are part of the component description (`yak.yml`), not
> part of a language SDK.**
>
> Every SDK exposes the same abstraction (`sdk.store()`) regardless of the
> implementation language.
>
> The mapping from a component to a physical store is performed by the
> runtime deployment and is therefore identical for Python, Ruby, .NET, Go,
> or any future host.

The consequence is visible at every level:

```
Pack (Python)      stores: [crm]   →   sdk.store("crm")
Pack (Ruby)        stores: [crm]   →   sdk.store("crm")
Pack (.NET)        stores: [crm]   →   sdk.Store("crm")
Pack (Go)          stores: [crm]   →   sdk.Store("crm")
```

The `yak.yml` is the same file in every case; only the SDK call is
idiomatic per language. No SDK knows *which* store lies behind the
abstraction — that is runtime and deployment knowledge.

This is what makes the decision stable in time: a Ruby host written in five
years reads the same `yak.yml`, a .NET host reads the same `yak.yml`, and
the `yak` tool works unchanged. The ADR fixes the contract at the component
level — the level every host already shares — so it does not need to change
when a new host language arrives.

## Four Layers of Store Knowledge

Store knowledge is not one thing — it is four things, and each belongs to a
different owner. This is the same separation Docker, Kubernetes, and
ASP.NET make between the image, the manifest, and the injected secret.

### 1. Pack — versioned

The pack declares the logical names it works against and nothing more:

```yaml
stores:
  - crm
```

That is the entire contract. The pack does not even say which backend a
store is — ``crm`` is the shared term between pack, runtime, and
deployment. The pack is portable: hand it to anyone, they install it, and
the store is built from their deployment — never from a DSN committed to
Git.

### 2. Runtime — versioned

The runtime config holds only what the runtime itself needs to run:
network, ports, scheduling, logging, transport. It does **not** list
stores — the runtime is an executor, not a store registry. It runs packs;
the packs' commands use stores; the runtime is indifferent to which ones.
What the runtime *does* collect is the set of logical store names the
installed packs declare — `{crm, security, telemetry}` — so its store
registry knows which names must exist.

```
runtime:
  host: 0.0.0.0
  port: 9100
  logging: ...
```

### 3. Installation — not versioned, machine-specific

The installation decides the backend **and** the instance of each store.
It is created by `yak install` (which asks *"Store 'crm' — which backend?"*,
then *"where does it live?"*), lives outside Git (e.g.
`.yak/runtime/stores.yml`), and answers *"what is crm and where?"* — never
*"which DSN is in the repo?"*.

```yaml
stores:
  crm:
    backend: postgres
    host: db.company.local
    port: 5432
    database: crm
    username: stefan
    credential: company-postgres
```

The same pack installs on a Raspberry Pi with `backend: sqlite`, in a
company with a postgres cluster, and in Kubernetes with a managed database
— the pack never changes.

### 4. Secret store — never in Git

Passwords, tokens, and certificates never live in the pack, the runtime
config, or the installation. They live in a secret store the platform
knows: the OS keychain, the Linux Secret Service, Windows Credential
Manager, Vault, or a cloud secrets manager. The installation only
references the credential by name:

```yaml
stores:
  crm:
    credential: company-postgres
```

The four layers answer one question each: **what** (pack), **where the
runtime runs** (runtime), **what and where the store is** (installation),
**who may open it** (secret store). Nothing sensitive ever becomes part of
a pack or a Git repository.

## Consequences

### Benefits

- **Ownership chain intact.** Pack declares → tool prepares → runtime
  resolves → code is infrastructure-free. The exact line that already holds
  for `host`, `entry`, and `resources` now holds for persistence.
- **Commands orchestrate.** A command is application logic and may work
  against several stores — migration (MSSQL → crm), sync (crm → ident +
  telemetry), reporting (crm + security). Each is `sdk.store(name)`, no
  special case.
- **Packs stay portable.** A pack declaring `stores: [crm]` runs on any
  deployment that provides `crm` — postgres, sqlite, memory, or a future
  backend, chosen entirely by the deployment.
- **A pack uses stores, it does not own them.** The declaration lists the
  stores a pack's commands work against; the deployment decides what each
  name is. Ownership stays with the platform.
- **`sdk.events()` becomes possible.** Once multiple stores exist, an event
  service can project the runtime's activity events and any store's domain
  revisions into one chronology — the store declaration is what makes the
  word "any store" meaningful.

### Not part of this ADR

The following build *on* this ADR and are explicitly out of scope:

- Store router
- Multiple physical databases
- Event aggregation
- Replication
- Sharding

This ADR fixes the contract. The mechanisms are separate decisions.

### Trade-offs

- **Indirection.** `stores: [crm]` does not tell the reader which database it
  is. That is intentional — the reader of the pack learns a need, the
  reader of the deployment learns a database.
- **Name collisions are real.** Two packs declaring the same name share one
  store. That is a feature (shared store, ADR-17), but the namespace
  boundaries inside a shared store must stay explicit.

### Simpler or more complex?

- **Pack: simpler.** A list of names replaces an implicit global. The code
  calls `sdk.store(name)` and names a declared capability.
- **Runtime: unchanged for now.** Binding resolution is deferred until more
  than one store exists; today every name maps to the one store.
- **Operator: more structure.** The deployment gains a `stores:` section —
  the price of having more than one store at all.

## Rejected alternatives

### Configuring the store inside the pack

```python
StoreClient(...)
```

Rejected. Persistence is a runtime capability. A pack constructing a store
client owns infrastructure the platform owns.

### Store router first

Rejected. The contract comes first, the implementation second. A router
without a declared profile has nothing to route.

### A `default` store

Rejected. `sdk.store()` does not fall back to a default when several stores
are declared — it raises *"Multiple stores declared. Please specify a store
name."* Ambiguity is surfaced, never hidden. (Earlier versions of this ADR
introduced a default; the convenience of `sdk.store()` with exactly one
declared store makes a default unnecessary.)

## Open questions

1. **Who owns the `stores:` section?** The runtime configuration file, or a
   deployment-level file the `yak` tool maintains? The direction is now
   clear: not the runtime config (the runtime collects only store *names*)
   and not the pack (which declares only the names). The `stores:` section
   belongs to the deployment — created by `yak install`, machine-specific,
   not versioned.
2. **Where do stores' own needs live?** Retention, backend tuning — next to
   the store in the deployment. Whether they are per-store keys or a
   reference to a named backend definition is left open.
3. **Does the declared name constrain the namespace?** Does `stores: [crm]`
   imply a `crm/*` namespace inside the store, or do namespaces and store
   names vary independently? Default bias: independent — namespaces are the
   domain's dimension, the store name is the physical one.
4. **Is `crm` a profile or an identity?** The name describes the store's
   *identity* more than its configuration. If "profile" reads as a
   configuration concept, the term may later shift toward the store's
   logical identity (`stores: [crm]` = "the store that is crm"). The
   declaration is unaffected; only the vocabulary may settle later.
5. **How does the resolver bind without a declared store?** A pack with no
   `stores:` entry has no name to resolve against. Does it bind to the
   deployment's single store (today the only one), or is the declaration
   required once several stores exist? Default bias: no declaration binds
   to the deployment's default store, preserving today's behavior.

## Implementation sketch (for later)

**Not built yet — this ADR fixes the decision, not the code.**

1. **Parser.** Accept `stores: <list of names>` in the pack manifest;
   validate each entry is a scalar name. Packs without it get the default.
2. **`yak` tooling.** On install, read the declaration, resolve against the
   deployment `stores:`, create the entry when missing. No pack change.
3. **Runtime binding.** `sdk.store(name)` resolves the declared name — while
   a single physical store exists, every name maps to it; the mapping
   arrives with the store router. `sdk.store()` with exactly one declared
   store returns it; with several it raises.
4. **Tests.** A pack declares `stores: [crm, telemetry]`, installs, and its
   `sdk.store("crm")` / `sdk.store("telemetry")` writes land in the
   respective stores; a pack without a declaration keeps binding to the
   default; two packs with the same name share one store.
