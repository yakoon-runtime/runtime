# Deployment

Deployment decides how the abstract resources a capability needs are
bound in *this* installation. A capability declares *that* it needs a
store; the deployment decides *which* store it gets.

```text
Capability
  declares logical store "ident"
             │
             ▼
      yak configure ident
             │
      ┌──────┴──────┐
      │             │
   memory        postgres
                     │
              env://IDENT_DATABASE
                     │
                     ▼
               deployment.yml
                     │
                     ▼
                  Runtime
```

## What a store is

A store is the persistent resource a capability needs: event storage for
documents, plus a sequencer for generated ids. Capabilities do not know
*where* their store lives — they only declare the logical store by name
(`ident`, `contacts`, `worlds`, …). The runtime resolves each declared
store through the deployment.

This is the ownership boundary:

```text
Capability:     "I need a store named ident"
deployment.yml: "In this installation ident is realized by
                 EventStoreFactory over PostgreSQL"
Runtime:        "I resolve that binding and build the store."
```

No capability configures a backend, and no global backend is configured
for the whole platform. Each store is bound per installation — `ident`
can be PostgreSQL while `contacts` and `worlds` stay in memory.

## deployment.yml

`.yak/deployment.yml` is the operator's file. It holds the actual
binding decisions of one installation:

```yaml
stores:
  ident:
    factory: y5n.runtime.store.event.wire:EventStoreFactory
    config:
      backend: postgres
      dsn: env://IDENT_DATABASE
```

It is created and edited by `yak configure` (never by capability code),
it is honored by install/update, and it survives them. It is written
*before* provisioning runs, so a failed provisioning leaves the
decision visible and correctable.

## memory vs. postgres

- **memory** — the default after installation. Nothing is persisted;
  the store lives as long as the runtime process.
- **postgres** — persistence in an existing PostgreSQL server. The
  factory performs provisioning against that server.

Changing a binding is `yak configure <store>`; pressing Enter keeps the
current value, so the same command both initially sets up and later
edits a store.

## Configuration and env://

A DSN can be given as a literal connection string or as an
`env://NAME` reference to an environment variable:

```bash
export IDENT_DATABASE='postgresql://postgres:secret@localhost:5432/yakoon_demo'
yak configure ident
```

The factory resolves `env://NAME` from the runtime's environment. The
deployment file therefore never needs to hold a secret — for
production-style deployments, `env://` is the recommended form.

The configuration language belongs to the store factory
(`EventStoreFactory`); the capability and the runtime never see it.

## Provisioning

Provisioning materializes what the chosen backend requires — the store
tables and the sequencer's id shards. It is idempotent and runs as part
of `yak configure`, inside the installation's own environment.

When the target database does not exist, configure asks the operator
whether to create it, then retries provisioning.

## Missing secrets fail fast

If `deployment.yml` references `env://IDENT_DATABASE` but the variable
is not set, runtime start fails immediately with a clear error:

```text
RuntimeError: EventStoreFactory: dsn environment variable not set: IDENT_DATABASE
```

There is **no silent fallback** to memory or to any other backend — a
store bound to PostgreSQL never quietly degrades. The missing
environment variable is an operator error and must be fixed before the
runtime starts.