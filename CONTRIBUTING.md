# Contributing to Yakoon

## Development Setup

```bash
git clone <repo>
cd yakoon
python -m venv .venv
source .venv/bin/activate
pip install -e apps/y5napp-runtime
pip install -e apps/y5napp-textual
```

## Code Style

- **Formatter**: Black
- **Linter**: Ruff
- **Type checker**: Pyright

Run before committing:

```bash
ruff check .
pyright
```

## Architecture Decisions

Decisions are documented in [docs/DECISIONS.md](docs/DECISIONS.md).

If you make an architectural decision, add an entry there. The rule: **document what and why** — not how.

## Testing

Tests use pytest with asyncio mode. See [docs/TESTING.md](docs/TESTING.md) for the full strategy.

```bash
pytest
```

## Project Structure

```
apps/           — Runnable applications (runtime, textual, web)
runtime/        — Core runtime packages
stores/         — Storage backends (event store)
spaces/         — Domain spaces (shell, identity, runtime)
transports/     — Transport layers
docs/           — Documentation (active)
docs/archive/   — Historical documentation
```

## Pull Request Guidelines

1. One feature/fix per PR
2. Add tests for new code when possible
3. Run linting and type checking
4. Update docs if architecture changes
5. Keep the decision log current
