# ADR 19: Declarative Deployment

**Status: Proposed**

The next experiment. ADR-18 proved that a pack can declaratively describe
the logical stores it uses, without knowing infrastructure. This ADR asks
the second half of the story: **how does a collection of declarative packs
become a running installation?**

The answer is the **deployment model** — the mapping between logical
stores and physical resources. The `yak` tool becomes the assembler that
materializes the deployment from the packs' declared needs.

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

> **Assembler** — the role of `yak`: it collects the declared needs of all
> installed packs and materializes the deployment that satisfies them.

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

1. **Who knows the backend list?** Which backends exist (postgres, sqlite,
   memory) — does `yak` know it, or does the deployment declare it?
2. **Where do credentials live?** Four Layers (ADR-18): a secret store,
   never in pack or deployment. How does the deployment reference a secret?
3. **When do migrations run?** First `install`, `update`, runtime start?
   Who owns migration logic — the pack or the deployment?
4. **What happens on update?** A new pack adds stores — existing resources
   stay untouched?
5. **What happens on uninstall?** The physical database stays (data does
   not belong to the pack)?
6. **Where is the deployment file?** Not versioned, machine-specific —
   `.yak/runtime/stores.yml`, owned by `yak`?

## Implementation sketch (for later)

**Not built yet — this ADR fixes the direction, not the code.**

1. **Enforce declared access.** `StoreResolver` raises when
   `store_name` is not in the node's declared stores (dependency check).
2. **Deployment model.** A mapping file (logical store → physical
   deployment) owned by `yak`, machine-specific, not versioned.
3. **`yak install`.** Collect declared stores, guide the mapping
   (new/existing, which), write the deployment.
4. **Tests.** A pack cannot reach an undeclared store; two packs share one
   declared store; the deployment maps several logical stores to one
   physical resource.
