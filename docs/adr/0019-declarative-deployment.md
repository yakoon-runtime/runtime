# ADR 19: Declarative Deployment

**Status: Accepted**

ADR-18 proved that a pack can declaratively describe the logical stores it
uses, without knowing infrastructure. This ADR answers the second half of
the story: **how does a collection of declarative packs become a running
installation?**

The answer is the **deployment model** — the mapping between logical
stores and physical resources. The `yak` tool is the assembler that
materializes the deployment from the packs' declared needs. The core is
implemented and proven end to end: the resolver enforces the dependency
list, `yak install` assembles `deployment.yml`, and the runtime refuses to
start without an installation — no silent fallback, no guessed deployment
information.

> **A pack declares what it depends on. `yak` assembles the deployment.
> The runtime executes. The SDK stays minimal.**

## Key sentence

> **A store is always logical; a database is physical. The deployment maps
> the one to the other.**
>
> Capability names are globally unique, but access is pack-local: a pack
> can only use the stores it declares. `stores:` is a dependency list, not
> a registry.

## Vocabulary

> **Store** — a logical, named capability (`crm`, `telemetry`). Global in
> meaning, pack-local in access. Never a database.

> **Deployment** — the physical reality a logical store is mapped to
> (`postgres-main`, `analytics`). Owned by the installation, not by any
> pack.

> **Installation** — the machine-specific product of the assembler: the
> mapping of logical stores to deployments, plus the references to
> secrets. Not versioned. Consumed by the runtime — `yak` does not write
> runtime configuration, it writes an installation.
>
> An installation is an **artifact**, not a file. The YAML is only its
> representation. In time the installation grows beyond the deployment:
> installed packs, versions, migration state, certificates, queue and
> search bindings. It is the assembled, machine-specific representation of
> a Yakoon platform — the runtime tree describes the application, the
> installation describes the platform.

> **Assembler** — the role of `yak`: it collects the declared needs of all
> installed packs and materializes the installation that satisfies them.

The rule is the same as for ports: **capability names are globally unique,
but every pack explicitly declares which capabilities it uses.**

## Context

### ADR-18 ended at the pack

ADR-18 proved the chain from `stores:` to `sdk.store("crm")` with no
infrastructure knowledge anywhere. The experiment is validated. What it did
**not** answer is where the physical stores come from. Today persistence
runs on engine defaults (`memory`); the space configs
(`docs/config/spaces/*.yml`) are an unwired predecessor — hand-written,
named per pack, never loaded.

### Two axes, not one

The key question — *is a logical store globally unique?* — resolves into
two separate axes:

| Axis | Answer |
|---|---|
| Meaning of the name | global — `crm` is `crm` everywhere (a port name) |
| Permission to access | pack-local — a pack can only use declared stores |

A name collision is deliberate sharing (two packs declaring `crm` share
the one store, ADR-17), but a pack can never reach an *undeclared* store.

### The pack describes its dependencies

`stores:` is a dependency list:

```yaml
# Reporting depends on CRM and telemetry
stores:
  - crm
  - telemetry
```

```yaml
# A migration orchestrates between CRM and legacy
stores:
  - crm
  - legacy
```

## Problem

1. **Persistence is configured, not deployed.** DSNs and backends are
   hand-written, unloaded, and duplicated across packs.
2. **No one answers "which database exists?"** The mapping from logical
   store to physical resource has no owner.
3. **Undeclared access is unenforced.** A command could reach any store;
   `stores:` should be a dependency contract with enforcement.
4. **Store and database are conflated.** The platform must keep them apart,
   or the model collapses into "a store is a postgres".

## Decision

### 1. Store ≠ Database

A **store** is logical and globally meaningful; a **database** is physical
and deployment-local. Multiple logical stores may map to one physical
resource; one logical store maps to exactly one deployment.

```
crm ──────┐
           ├──► postgres-main
ident ────┘

telemetry ──► analytics (clickhouse)
```

### 2. The deployment owns the mapping

The pack declares names only. The deployment decides which physical
resource each name is. The mapping is 1:n (logical → physical), owned
entirely by the deployment:

```yaml
deployments:
  postgres-main:
    backend: postgres
  analytics:
    backend: clickhouse
```

### 3. `stores:` is a dependency list

A pack may only use the stores it declares. `sdk.store("x")` from a pack
without `x` in `stores:` is an error — an undeclared dependency, like an
`import` whose module is not in the requirements.

### 4. `yak` assembles, it does not guess

`yak` collects the declared stores of all installed packs, then guides the
administrator through the mapping: *new resource or existing? which one?*
It never searches databases, knows no naming conventions, no `yakoon_crm`
heuristics. The administrator knows more than the tool.

### 5. The product is an installation, not runtime configuration

`yak` writes **no configuration for the runtime.** It writes an
**installation** — the machine-specific product of the assembler, kept
outside Git (e.g. `.yak/installation/`):

```yaml
# .yak/installation/deployment.yml
stores:
  crm:
    deployment: postgres-main
  ident:
    deployment: postgres-main
  telemetry:
    deployment: analytics

deployments:
  postgres-main:
    backend: postgres
    secret: postgres-main
  analytics:
    backend: clickhouse
    secret: analytics
```

Secrets are not here — only references. The installation points at the
secret store (`secret: postgres-main`); the secret itself (host, port,
user, password, ssl) lives in the platform's secret store.

The runtime **consumes** the installation at startup: it reads the
mapping, asks the secret store for each referenced secret, and builds the
store registry from it. The runtime never learns *why* crm and ident share
postgres-main or *why* telemetry uses clickhouse — it receives a finished
store registry.

The same installation reads on any machine. A notebook maps `crm` to
sqlite, a server maps it to a postgres cluster — same pack, same runtime,
a different installation.

## Consequences

### Benefits

- **Packs are self-describing.** Every infrastructure dependency is
  declared; nothing is assumed.
- **The deployment is the only place that knows databases.** One mapping,
  one owner.
- **Enforcement for free.** Undeclared access fails loudly.
- **The platform grows.** The same model later covers queues, caches,
  search, secrets — each a capability with a global name and pack-local
  access.

### Trade-offs

- **A new layer.** The deployment adds indirection between pack and
  runtime — the price of a mapping owned by the installation.
- **The pack must declare to share.** Sharing a store requires both packs
  to name it — explicit, but slightly more words.

### Simpler or more complex?

- **Pack: the same.** `stores:` already exists.
- **Runtime: unchanged.** The resolver already reads `node.stores`; only
  the *enforcement* of declared access is added.
- **Operator: more structure.** A deployment file, owned by `yak`, holds
  the mapping.

## Open questions

The open questions are not leftovers — they define the platform. Ordered
by dependency: the migration questions first, because their answers unlock
most others.

1. **Who owns migrations?** The pack — it knows its data model; `yak` and
   the runtime do not. `yak` only *executes* migrations. The migration
   status becomes part of the installation (see Q3).
2. **When do migrations run?** Not at runtime start (the runtime changes
   nothing), not on first access (too magical), but at the assembler:
   `yak install` and `yak update` run migrations. Deployment changes
   infrastructure; the runtime only executes.
3. **Who knows the backend list?** Neither `yak` nor the deployment —
   **capability providers do.** Backends are packs (`y5n-store-postgres`,
   `y5n-store-sqlite`, `y5n-store-clickhouse`). `yak` asks only: *"which
   store backends are installed?"* — the same chain one level deeper.
   Which backends the platform supports is **not an architecture
   decision** — it is defined separately by the platform (a list of
   supported store backends), documentation rather than a decision this
   ADR must make.
4. **Where do credentials live?** Four Layers (ADR-18): a secret store,
   never in pack or deployment. The installation never knows credentials —
   only references (`secret: postgres-main`); the secret store resolves
   host, port, username, password, ssl, certificate.
5. **What happens on update?** `yak update` asks only for newly declared
   stores (`analytics`); existing deployments stay untouched.
6. **What happens on uninstall?** Data never belongs to the pack. The
   physical database stays; at most a warning that a deployment is no
   longer referenced (*Delete? [y/N]*). Never automatic.
7. **Who owns the schema and migrations of a shared logical store?**
   Access is settled (`stores:` grants it), but evolution is not. Two
   packs sharing `crm` — who defines its tables, views, indices, schema
   changes? The pack owning the schema outright (variante A) seems wrong;
   a store carrying its own schema with packs contributing (variante B),
   or packs owning migrations executed in a defined order by `yak`
   (variante C, like Flyway/Liquibase), are the candidates. Likely the
   seed of ADR-20.

## Capability Provider

The platform gains a fifth actor. A **capability provider** is the
entity that *provides* a capability for Yakoon — postgres, sqlite,
clickhouse are not known to `yak` or the runtime; someone provides them.
It is neither pack nor runtime nor installation — it is the answer to Q3:

> **Not `yak` knows backends — capability providers do.**

A provider may itself be a pack (`y5n-store-postgres`). The chain becomes:

```
Pack (declares) → yak (assembles) → Installation (mapping)
      → Capability Provider (provides) → Runtime (executes) → SDK (uses)
```

## Implementation sketch (for later)

**Not built yet — this ADR fixes the direction, not the code.**

1. **Enforce declared access.** `StoreResolver` raises when
   `store_name` is not in the node's declared stores (dependency check).
2. **Installation model.** `.yak/installation/deployment.yml` — the
   mapping (logical store → deployment) plus deployment definitions
   (backend, secret reference). Owned by `yak`, machine-specific, not
   versioned.
3. **Runtime consumption.** At startup the runtime reads the installation,
   resolves secrets through the secret store, and builds the store
   registry from it — it never configures itself.
4. **`yak install`.** Collect declared stores, guide the mapping
   (new/existing, which), write the installation.
5. **Tests.** A pack cannot reach an undeclared store; two packs share one
   declared store; the deployment maps several logical stores to one
   physical resource; the same pack installs as sqlite on one machine and
   postgres on another.
