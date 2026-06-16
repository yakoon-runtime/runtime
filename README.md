# Yakoon — Operative Runtime for Semantic Spaces

Yakoon is a server-driven, event-sourced UI runtime with deterministic projection. It is an **operative runtime** — not a framework, not a platform, not an application server.

## Why Yakoon?

Most software is built around the assumption that **data must go to the application**. Yakoon inverts this: **the runtime goes to the data.**

Yakoon defines:
- **What** can be done (commands per space/node)
- **Who** can do it (permissions, roles)
- **How** it is presented (deterministic projection → any UI)
- **Which** AI handles which domain (pluggable per space)

It is designed for small, specialized, local AI models per domain — not one centralized model.

## Core Architecture

```
Flow → State → Projection → UI
```

- **Flow** — State machine (async generators)
- **State** — Deterministic, immutable
- **Projection** — Pure function: `projection = f(state)`
- **Client** — Any UI (console, web, TUI, SSH)

## Quick Start

```bash
pip install -e apps/y5napp-runtime
pip install -e apps/y5napp-textual

yakoon-runtime 9100     # Terminal 1: Runtime
yakoon-texture           # Terminal 2: TUI client
```

See [docs/GETTING_STARTED.md](docs/GETTING_STARTED.md) for details.

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

See [LICENSE](LICENSE) or the `pyproject.toml` in each package.
