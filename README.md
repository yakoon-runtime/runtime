# Yakoon — Operative Runtime for Long-running Flows

Yakoon is a deterministic runtime for flows, state, and projections. It is an **operative runtime** — not a framework, not a platform, not an application server.

An operative runtime owns execution, context, and state. Clients merely observe and interact with it.

Clients are transient. The runtime is the source of truth.

## Core Architecture

```
Flow → State → Projection → UI
```

- **Flow** — Executable state machine (async generators)
- **State** — Deterministic, captures decisions
- **Projection** — Pure function: `projection = f(state)`
- **Client** — Any UI (console, web, TUI, SSH); never owns state

## Why Yakoon?

Most software sends **data to the application**. Yakoon sends **the runtime to the data**.

Sessions may outlive clients. Flows may outlive sessions. Runtime, not UI, is the persistent layer.

This makes long-running work observable, resumable, and independent of individual clients.

## Quick Start

```bash
pip install -e apps/y5napp-runtime
pip install -e apps/y5napp-textual

yakoon-runtime 9100     # Terminal 1: Runtime
yakoon-texture           # Terminal 2: TUI client
```

See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for details.

## AI Integration

AI is a capability, not the product. Yakoon can connect different AI models per domain — small local models for sensitive data, large cloud models for creative work. The runtime decouples AI from infrastructure.

See [docs/MANIFEST.md](docs/MANIFEST.md) for the full reasoning.

## Documentation

| Document | Purpose |
|----------|---------|
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | Core architecture & philosophy |
| [DECISIONS.md](docs/DECISIONS.md) | Architecture decision record |
| [MANIFEST.md](docs/MANIFEST.md) | Why Yakoon exists |
| [TESTING.md](docs/TESTING.md) | Testing strategy |
| [GETTING_STARTED.md](docs/GETTING_STARTED.md) | Setup & usage |
| [CONTRIBUTING.md](CONTRIBUTING.md) | How to contribute |

## License

Apache 2.0. See [LICENSE](LICENSE).
