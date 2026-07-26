# Yakoon — Getting Started

## Apps Overview

| App | Install | Start |
|-----|---------|-------|
| `y5n-apps-runtime` | `pip install -e apps/y5n-apps-runtime` | `yakoon-runtime 9100` or `python -m y5n.packs.runtime` |
| `y5n-apps-shell` | `pip install -e apps/y5n-apps-shell` | `yakoon-shell` or `python -m y5n.packs.shell` |
| `y5n-apps-web` | `pip install -e apps/y5n-apps-web` | `yakoon-web 8000` or `python -m y5n.packs.web` |

## Dev Setup (one-time)

```bash
pip install -e apps/y5n-apps-runtime
pip install -e apps/y5n-apps-shell
pip install -e apps/y5n-apps-web
```

Or via `scripts/install.sh`.

## Example

```bash
# Terminal 1: Runtime
yakoon-runtime 9100

# Terminal 2: Texture
yakoon-shell

# Terminal 3 (optional): Web client
yakoon-web 8000
```

## Module vs Package

| PyPI Name | Module Name |
|-----------|-------------|
| `y5n-apps-runtime` | `y5n.packs.runtime` |
| `y5n-apps-shell` | `y5n.packs.shell` |
| `y5n-apps-web` | `y5n.packs.web` |

The PyPI name (`y5n-apps-web`, with hyphen) is used for `pip install`.
The module name (`y5n.packs.web`, with dot) is used for `python -m`.
