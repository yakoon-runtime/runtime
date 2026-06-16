# Yakoon — Getting Started

## Apps Overview

| App | Install | Start |
|-----|---------|-------|
| `y5napp-runtime` | `pip install -e apps/y5napp-runtime` | `yakoon-runtime 9100` or `python -m y5napp.runtime` |
| `y5napp-textual` | `pip install -e apps/y5napp-textual` | `yakoon-texture` or `python -m y5napp.textual` |
| `y5napp-web` | `pip install -e apps/y5napp-web` | `yakoon-web 8000` or `python -m y5napp.web` |

## Dev Setup (one-time)

```bash
pip install -e apps/y5napp-runtime
pip install -e apps/y5napp-textual
pip install -e apps/y5napp-web
```

Or via `scripts/install.sh`.

## Example

```bash
# Terminal 1: Runtime
yakoon-runtime 9100

# Terminal 2: Texture
yakoon-texture

# Terminal 3 (optional): Web client
yakoon-web 8000
```

## Module vs Package

| PyPI Name | Module Name |
|-----------|-------------|
| `y5napp-runtime` | `y5napp.runtime` |
| `y5napp-textual` | `y5napp.textual` |
| `y5napp-web` | `y5napp.web` |

The PyPI name (`y5napp-web`, with hyphen) is used for `pip install`.
The module name (`y5napp.web`, with dot) is used for `python -m`.
