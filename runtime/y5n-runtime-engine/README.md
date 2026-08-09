# y5n-runtime-engine

The runtime engine — the executor that runs Yakoon's packs.

## The Yakoon Platform Model

> **A pack describes what it needs. The platform decides how that need is
> met.**

Yakoon's architecture can be drawn on one page:

```
            Pack
     (describes its needs)
             │
             ▼
       yak Assembler
 (materializes the needs)
             │
             ▼
    Runtime Services
(Store, Host, Resources, …)
             │
             ▼
             SDK
```

The four roles never overlap:

- **Pack** — describes its capabilities and needs declaratively
  (`host:`, `store:`, `resources:`; later `queue:`, `cache:`,
  `scheduler:`).
- **Assembler** (`yak`) — collects the needs of all installed packs and
  builds the deployment that satisfies them. It is not an installer of
  files; it is the assembler of a runtime environment.
- **Runtime** — provides the services (store, host, resources). It does
  not know which pack asks and does not know infrastructure.
- **SDK** — the minimal, stable surface the pack code sees
  (`sdk.store()`, …).

### The recurring pattern

Almost every architecture decision reduces to one chain:

```
Pack describes need
        │
        ▼
Assembler fulfills need
        │
        ▼
Runtime provides capability
        │
        ▼
SDK stays minimal
```

The store is the first capability to follow it fully. The same shape holds
for `host`, `resources`, and `entry` — and will be reused for caches,
queues, schedulers, and any future runtime service.

### The runtime gets smaller

The runtime does not own PostgreSQL. It owns a **store service**. Whether
that service is backed by PostgreSQL, SQLite, or memory is the deployment's
decision, not the runtime's:

```
The runtime owns a store service
        │
        ▼
backend = postgres | sqlite | memory   (deployment decides)
```

### Store profiles (ADR-18)

A pack declares its store by a logical name, never by infrastructure:

```yaml
store: crm
```

Four layers of store knowledge — each belongs to a different owner:

| Layer | Owns | Content | Versioned |
|-------|------|---------|-----------|
| **Pack** | the name | `store: crm` | yes |
| **Runtime** | its own config | network, ports, logging | yes |
| **Installation** | the instance | `stores: crm: backend: postgres` + host, port, db | no |
| **Secret store** | the credentials | referenced by name, never in Git | no |

The runtime collects the logical store names the installed packs declare
and builds its registry from them. What each name means is deployment
knowledge — assembled by `yak`.
