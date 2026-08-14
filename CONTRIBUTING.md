# Contributing to Yakoon

## Development Setup

```bash
git clone <repo>
cd runtime
python -m venv .venv
source .venv/bin/activate
pip install \
  -e packages/y5n-runtime-api \
  -e packages/y5n-runtime-engine \
  -e packages/y5n-runtime-store \
  -e packages/y5n-runtime-transport \
  -e packages/y5n-runtime-llm \
  -e packages/y5n-runtime-boot \
  -e packs/y5n-packs-root
pip install -r requirements-dev.txt
```

## Commit Conventions

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>
```

**Common types:** `feat`, `fix`, `refactor`, `docs`, `style`, `test`, `chore`

Examples:
```
feat(cli): add project init command
fix(auth): reject empty passwords
refactor(realm): move phase logic to store
docs(readme): update getting started
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
pip install -r requirements-dev.txt
pytest
```

## Project Structure

```
packages/       — Core runtime packages (api, engine, store, transport, llm, boot)
packs/          — Installable content packs (root)
brand/          — Logos and social assets
docs/           — Documentation (active)
docs/archive/   — Historical documentation
```

## Pull Request Guidelines

1. One feature/fix per PR
2. Add tests for new code when possible
3. Run linting and type checking
4. Update docs if architecture changes
5. Keep the decision log current
