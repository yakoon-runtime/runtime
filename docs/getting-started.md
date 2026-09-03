# Getting Started with Yakoon

Yakoon is an operating environment for integrations. You install
capabilities, configure the resources they need, start and use them —
from the terminal.

This guide takes you from an empty machine to a running Yakoon with a
persistent store: the runtime, the system command set, the shell, and
identity backed by PostgreSQL.

```text
Install capabilities
        │
        ▼
Configure the resources they need
        │
        ▼
Start Yakoon
        │
        ▼
Use them
```

## 1. Install Yak

Prerequisites: Python ≥ 3.11, and a reachable PostgreSQL server for the
store part of this guide.

```bash
pip install yakoon
```

`yak` becomes available and manages the rest of the installation.

## 2. Create an installation

```bash
mkdir yakoon-demo
cd yakoon-demo
```

## 3. Install capabilities

An installation starts empty. Every install adds a capability — `runtime`
is the engine, `system` the base command set, `ident` identity and
permissions, `shell` the interactive shell:

```bash
yak install runtime
yak install system
yak install ident
yak install shell
```

Yak resolves components through the official Yakoon distribution; the
installation remembers it for subsequent installs.

### Alternative distributions

By default Yak installs from the official Yakoon distribution. To resolve
from a different distribution — for development, staging or your own
component set — pass its index URL explicitly:

```bash
yak install runtime \
  --distribution https://raw.githubusercontent.com/yakoon-runtime/dists/main/distribution.yml
```

The flag overrides the default for this install (repeatable, later wins).

## 4. Connect identity to PostgreSQL

`ident` keeps accounts, groups and permissions in a logical store called
`ident`. By default that store is in memory. Bind it to PostgreSQL with
`yak configure`, referencing the connection string through an environment
variable so no secret goes into the configuration:

```bash
export IDENT_DATABASE='postgresql://postgres:secret@localhost:5432/yakoon_demo'
yak configure ident
```

Answer the prompts:

```text
Backend for store 'ident' [memory/postgres] (memory): postgres
DSN for store 'ident' (literal or env://NAME) (env://IDENT_DATABASE):     ← press Enter
```

If the database does not exist, Yak asks and creates it for you. The
store schema is provisioned, and `deployment.yml` now references only
`env://IDENT_DATABASE` — the connection string stays in your shell.

## 5. Start Yakoon

```bash
yak runtime start
```

## 6. Your first session

```bash
yak shell
```

Inside the shell, log in as the built-in administrator, move to the
ident area, and list the accounts this fresh `ident` seeded:

```text
su root --password master
cd /usr/sbin/ident
account/list
```

You should see three accounts:

```text
Accounts:
lara (Lara)
root
stefan (Stefan Bergmann)
```

You now have Yakoon running with a persistent identity store — and you
have seen its working surface: installation, capabilities, stores,
deployment, runtime and the shell.

## See also

- [Deployment](concepts/deployment.md) — what a store is, who decides
  how it is bound, and how `env://` keeps secrets out of configuration.
- [Concepts](concepts/) — how Yakoon works as a product.
- [Commands](reference/cli.md) — the concrete `yak` surface.