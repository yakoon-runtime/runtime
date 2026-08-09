# ADR 18: Declarative Store Profiles

**Status:** Proposed

> **The pack describes what it needs. The platform decides how that need
> is met.**
>
> A pack declares its persistence need as a named store profile —
> `store: crm`. The `yak` tool translates the need into deployment
> configuration; the runtime binds `sdk.store()` to the declared store;
> the code never knows infrastructure.

## Key sentence

> **A pack declares its store as a named profile, never as
> infrastructure.** `store: crm` says *"this pack works against the store
> profile called crm"* — which backend that is, where it lives, how it is
> tuned, is the deployment's decision. The code stays forever
> `store = sdk.store()`.
>
> **A declaration names a capability; it never selects an implementation.**

The second sentence is the general form of the first — and of the whole
Yakoon line of capability declarations: `host`, `resources`, `entry`, and
now `store` each name a capability, and none of them selects an
implementation.

## Vocabulary

> **Store profile** — what a pack declares about its persistence: a single
> logical name (`crm`, `security`, `telemetry`). A profile is a *need*, not
> a *specification*: it names a store, it never configures one.

> **Logical name** — the identifier the pack, the `yak` tool, and the
> deployment share. The deployment maps it to a physical store; the pack
> never sees the mapping.

> **Deployment** — the configuration that decides *how* a declared need is
> fulfilled: which backend, which DSN, which retention. It is the only
> place in the system that knows infrastructure.

The declaration is a sibling of the other pack-level needs, and it is as
minimal as they are:

```
host: python        → which interpreter runs my nodes
entry:              → which files are my entry points
resources:          → which assets I ship
store: crm          → which store my writes and reads go to
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

### 1. A pack declares `store: <name>` — a named profile, nothing more

`yak.yml` gains one top-level key:

```yaml
store: crm
```

Meaning: *this pack needs persistence, and its persistence is the store
profile logically named `crm`.* That is the entire contract. No nested
object, no backend, no connection, no retention.

Should a later pack ever need to express more than a single name, the same
key opens up to a structured form:

```yaml
store:
  profile: crm
```

The decision fixes the *principle* — declare a profile, not
infrastructure — and deliberately leaves the scalar form as the current
syntax.

### 2. The pack knows only the name

The pack declares the store's **logical name** and nothing else — not the
backend, not the instance. It does not even say whether the store is
postgres, sqlite, or memory:

```yaml
# never
store:
  backend: postgres
  host: db.company.local
  port: 5432
  database: crm
  username: stefan
  connection: postgres://...
  retention: 30d
```

The backend is *also* a realization, not a need — ``store: crm`` says "I
need the store called crm", and it is the deployment's decision whether
that is a postgres cluster, a sqlite file on a Raspberry Pi, or a managed
database in a Kubernetes cluster. The pack describes its need; the
deployment describes the store (see *Four Layers of Store Knowledge*).

### 3. The code stays `sdk.store()`

The pack code does not change and gains no argument:

```python
from y5n.sdk import store

db = store()
```

The runtime binds `db` to the store profile the pack declared.
`sdk.store("crm")` is never introduced — the pack does not name its store in
code, it names it in its declaration.

### 4. The `yak` tool translates need into deployment

`yak install` reads `store: crm`, and asks: *"Store 'crm' — which
backend?"* (postgres, sqlite, memory). If the store already exists in the
deployment configuration → does nothing; if it does not exist → asks the
backend and instance, then adds it:

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
them. Installing three packs (`crm` → `store: crm`, `ident` → `store:
security`, `telemetry` → `store: telemetry`) yields three logical stores in
the deployment — and only then does the tool decide which already exist,
which to create, which to migrate. The store is the first capability this
mechanism serves; hosts, caches, queues, and schedulers follow the same
path. The pack never creates a database, opens a connection, or runs a
migration — it says "I need this logical store", and the platform builds it.

### 5. Ownership

| Level | Responsibility |
|-------|----------------|
| **Pack** | describes the store profile it needs |
| **yak** | assembles the deployment from all installed packs' needs |
| **Runtime** | provides the store service |
| **SDK** | delivers `sdk.store()` |

### 6. Backward compatibility: a pack without `store:` uses the default

A pack that declares no store keeps working — it binds to the default store
(today, the only one). The declaration is additive: `store: crm` names the
store, no `store:` means "the default". A single-store deployment is simply
the degenerate case where every logical name maps to the same physical
store.

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
Pack (Python)      store: crm   →   sdk.store()
Pack (Ruby)        store: crm   →   sdk.store
Pack (.NET)        store: crm   →   sdk.Store()
Pack (Go)          store: crm   →   sdk.Store()
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

The pack declares the store's logical name and nothing more:

```yaml
store: crm
```

That is the entire contract. The pack does not even say which backend it
is — ``crm`` is the shared term between pack, runtime, and deployment. The
pack is portable: hand it to anyone, they install it, and the store is
built from their deployment — never from a DSN committed to Git.

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
- **Packs stay portable.** A pack written against `store: crm` runs on any
  deployment that provides `crm` — postgres, sqlite, memory, or a future
  backend, chosen entirely by the deployment.
- **Multi-store becomes representable.** `store: crm` and `store: security`
  can land on different physical stores without any pack change.
- **`sdk.store()` stays stable forever.** The SDK surface does not grow
  arguments; resolution happens behind it.
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

- **Indirection.** `store: crm` does not tell the reader which database it
  is. That is intentional — the reader of the pack learns a need, the
  reader of the deployment learns a database.
- **Name collisions are real.** Two packs declaring the same name share one
  store. That is a feature (shared store, ADR-17), but the namespace
  boundaries inside a shared store must stay explicit.

### Simpler or more complex?

- **Pack: simpler.** One scalar key replaces an implicit global. The code
  is unchanged.
- **Runtime: unchanged for now.** Binding resolution is deferred until more
  than one store exists; today every name maps to the one store.
- **Operator: more structure.** The deployment gains a `stores:` section —
  the price of having more than one store at all.

## Rejected alternatives

### `sdk.store("crm")`

Rejected. The pack code then knows infrastructure — it names its store at
access time instead of declaring it. A pack declares its need; it does not
choose its instance per call.

### Configuring the store inside the pack

```python
StoreClient(...)
```

Rejected. Persistence is a runtime capability. A pack constructing a store
client owns infrastructure the platform owns.

### Store router first

Rejected. The contract comes first, the implementation second. A router
without a declared profile has nothing to route.

## Open questions

1. **One store per pack, or many?** This ADR assumes a pack declares *the*
   store it works against. If a pack needs two (`crm` for data, `audit` for
   activity), the declaration needs a richer shape. Default bias: one store
   per pack; packs compose via shared stores.
2. **What is the default store's name?** Packs without `store:` bind to it.
   Does the default have a name (e.g. `default`) that the deployment can
   remap, or is it simply "the only store" until a deployment says
   otherwise? Default bias: an explicit `default` name, remappable.
3. **Who owns the `stores:` section?** The runtime configuration file, or a
   deployment-level file the `yak` tool maintains? The direction is now
   clear: not the runtime config (the runtime collects only store *names*)
   and not the pack (which declares only the name). The `stores:` section
   belongs to the deployment — created by `yak install`, machine-specific,
   not versioned.
4. **Where do stores' own needs live?** Retention, backend tuning — next to
   the store in the deployment. Whether they are per-store keys or a
   reference to a named backend definition is left open.
5. **Does the declared name constrain the namespace?** Does `store: crm`
   imply a `crm/*` namespace inside the store, or do namespaces and store
   names vary independently? Default bias: independent — namespaces are the
   domain's dimension, the store name is the physical one.
6. **Is `crm` a profile or an identity?** The name describes the store's
   *identity* more than its configuration. If "profile" reads as a
   configuration concept, the term may later shift toward the store's
   logical identity (`store: crm` = "the store that is crm"). The
   declaration is unaffected; only the vocabulary may settle later.

## Implementation sketch (for later)

**Not built yet — this ADR fixes the decision, not the code.**

1. **Parser.** Accept `store: <name>` in the pack manifest; validate it is
   a single scalar. Packs without it get the default.
2. **`yak` tooling.** On install, read the declaration, resolve against the
   deployment `stores:`, create the entry when missing. No pack change.
3. **Runtime binding.** Make `sdk.store()` resolve the declared name — while
   a single physical store exists, every name maps to it; the mapping
   arrives with the store router.
4. **Tests.** A pack declares `store: crm`, installs, and its `sdk.store()`
   writes land in the `crm` store; a pack without a declaration keeps
   binding to the default; two packs with the same name share one store.
