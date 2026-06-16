# Yakoon — Operative Runtime for Long-running Flows

Clients are transient. The runtime is the source of truth.

Sessions may outlive clients. Flows may outlive sessions.

```
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│   Texture   │  │     Web     │  │     SSH     │
│  (TUI)      │  │  (Browser)  │  │  (Terminal) │
└──────┬──────┘  └──────┬──────┘  └──────┬──────┘
       │                │                │
       └────────────────┼────────────────┘
                        │
                ┌───────▼────────┐
                │    Runtime     │
                │  Flows         │
                │  Sessions      │
                │  State         │
                └────────────────┘
```

Connect from any client. The runtime keeps working.

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

This makes long-running work observable, resumable, and independent of individual clients.

## Quick Start

```bash
pip install -e apps/y5napp-runtime
pip install -e apps/y5napp-textual

# Terminal 1: Runtime
yakoon-runtime

# Terminal 2: TUI client
yakoon-texture
```

### Package vs Module vs Executable

| Package (pip) | Python Module | Command |
|---|---|---|
| `y5napp-runtime` | `y5napp.runtime` | `yakoon-runtime` |
| `y5napp-textual` | `y5napp.textual` | `yakoon-texture` |

For development or debugging:

```bash
python -m y5napp.runtime
python -m y5napp.textual
```

See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for full setup details.

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
