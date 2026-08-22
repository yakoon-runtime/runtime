# Yakoon Runtime

[![Version](https://img.shields.io/badge/Version-0.8.0-blue.svg)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.13+-blue.svg)]()
[![Tests](https://github.com/yakoon-runtime/runtime/actions/workflows/tests.yml/badge.svg)](https://github.com/yakoon-runtime/runtime/actions/workflows/tests.yml)

**Status: Active development**

The execution environment behind Yakoon capabilities.

The Yakoon Runtime executes commands provided by installed packs and
provides the shared services they run against: identity, permissions,
stores, resources, hosts, scheduling, resolution, audit and lifecycle.

**Packs contain domain capabilities. The runtime contains mechanisms.**

```text
              Commands / Capabilities
                       │
                       ▼
        ┌─────────────────────────────┐
        │       YAKOON RUNTIME        │
        │                             │
        │  Node Tree    Bus           │
        │  Resolver     Hosts         │
        │  Stores       Resources     │
        │  Permissions  Sessions      │
        │  Scheduler    Audit         │
        │  Ports        Sources       │
        └─────────────────────────────┘
                       │
                       ▼
          Execution · Persistence
          Resources · Integration
```

## Runtime Model

- **Node Tree** — the executable capability space, composed from mounted sources
- **Bus** — how commands and events travel between nodes
- **Resolver** — finds a capability by its address
- **Hosts** — provide the runtime for a capability
- **Stores** — persistence for capabilities
- **Resources** — shared assets and services
- **Permissions** — what an actor may do, enforced per call
- **Sessions** — interaction state, kept alive while clients come and go
- **Scheduler** — planned and deferred execution
- **Audit** — traceable changes
- **Ports** — the connection points capabilities expose

## Architecture

For the detailed model, decision record and the executor contract:

- [ARCHITECTURE](docs/architecture/overview.md)
- [DECISIONS](docs/adr/0000-decisions.md)
- [EXECUTOR](docs/architecture/executor.md)

## Links

- Developer setup: [`yakoon-runtime/developer`](https://github.com/yakoon-runtime/developer)
- SDK — write commands against the runtime: [`yakoon-runtime/sdk`](https://github.com/yakoon-runtime/sdk)

## License

Apache 2.0. See [LICENSE](LICENSE).
