# Yakoon — App-Start

| App | Install | Start |
|-----|---------|-------|
| `y5napp-runtime` | `pip install -e apps/y5napp-runtime` | `yakoon-runtime 9100` oder `python -m y5napp.runtime` |
| `y5napp-textual` | `pip install -e apps/y5napp-textual` | `yakoon-texture` oder `python -m y5napp.textual` |
| `y5napp-web` | `pip install -e apps/y5napp-web` | `yakoon-web 8000` oder `python -m y5napp.web` |

## Dev-Setup (einmalig)

```bash
pip install -e apps/y5napp-runtime
pip install -e apps/y5napp-textual
pip install -e apps/y5napp-web
```

Oder via `scripts/install.sh`.

## Beispiel

```bash
# Terminal 1: Runtime
yakoon-runtime 9100

# Terminal 2: Texture
yakoon-texture

# Terminal 3 (optional): Web-Client
yakoon-web 8000
```

## Module vs Package

| PyPI-Name | Modul-Name |
|-----------|-----------|
| `y5napp-runtime` | `y5napp.runtime` |
| `y5napp-textual` | `y5napp.textual` |
| `y5napp-web` | `y5napp.web` |

Der PyPI-Name (`y5napp-web`, mit Bindestrich) wird für `pip install` verwendet.
Der Modul-Name (`y5napp.web`, mit Punkt) wird für `python -m` verwendet.
