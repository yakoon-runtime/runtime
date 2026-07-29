# `yak create` — Scaffolding

## Problem

Users can install, build, and update packs, but cannot create new ones.
The development cycle starts at `build` instead of `create`.

## Design

Two separate commands build on each other:

```
yak create pack          →  Container (nichts ausführbar)
yak create command       →  Erster Command im Pack
```

Ein Pack ist ein Container für mehrere Commands. `create pack` erzeugt nur
die Hülle. `create command` fügt einen ausführbaren Knoten hinzu.

## `yak create pack <name>`

Erzeugt einen installierbaren Container — kein ausführbarer Command.

### Command

```
yak create pack <name> [--dir <path>]
```

### Output

```
<name>/
  pack.toml
  pyproject.toml
  src/
    y5n/
      packs/
        <name>/
          __init__.py
  structure/
    .yak/
      yak.yml
```

### `pack.toml`

```toml
name = "<name>"
version = "0.1.0"
description = "<Name> pack"
```

### `pyproject.toml`

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "y5n-packs-<name>"
version = "0.1.0"
requires-python = ">=3.13"
license = { text = "Apache-2.0" }
dependencies = ["y5n-runtime-api", "y5n-sdk-python"]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]
namespaces = true
```

### `src/y5n/packs/<name>/__init__.py`

Empty.

### `structure/.yak/yak.yml`

```yaml
title: <Title>        # Auto-capitalised

resolvable: false
navigable: true
contextual: false
```

Container node: `resolvable: false`, `navigable: true`. Kein `entry.run`.

---

## `yak create command <name>`

Fügt einen ausführbaren Command zum aktuellen Pack hinzu.

### Command

```
yak create command <name> [--pack <name>]
```

`--pack` ist optional. Ohne `--pack` wird das Pack automatisch erkannt:
1. `pack.toml` im CWD suchen
2. `pack.toml` in Elternverzeichnissen suchen (Git-ähnlicher Walk-up)

### Output (in ein bestehendes Pack)

```
structure/
  <name>/
    .yak/
      yak.yml
    resources/
      default.ydf
      man.ydf

src/
  y5n/
    packs/
      <packname>/
        <name>.py
```

### `structure/<name>/.yak/yak.yml`

```yaml
title: <Title>

resolvable: true
navigable: false
contextual: false
host: /boot/python/runtime

entry:
  run: pack:y5n.packs.<packname>.<name>:main

document:
  default: file:resources/default.ydf

man:
  default: file:resources/man.ydf
```

### `src/y5n/packs/<packname>/<name>.py`

```python
from y5n.sdk import context, ports, runtime


async def main():
    doc = ports.get("document")
    user = context.session().user or ""
    result = await doc.render(name="default", state={"user": user})
    await runtime.io.write(result)
```

### `resources/default.ydf`

```
{% if user %}{{ user }}{% else %}use 'su' to login{% endif %}
```

### `resources/man.ydf`

```
{{ title }} — short description
```

---

## `yak build` — Pack-Erkennung

`build` erkennt Packs nicht mehr über Namenskonventionen, sondern über
`pack.toml`:

1. `_find_buildable_projects` sucht nach Verzeichnissen mit `pack.toml`
2. `PythonBuildProvider.detect` prüft weiterhin `pyproject.toml`
3. Ein Verzeichnis mit `pack.toml` + `pyproject.toml` ist ein Python-basiertes Pack

---

## Full cycle

```bash
cd ~/dev/yakoon

yak create pack hello       # Container

cd hello
yak create command greet    # Erster Command

cd ..
yak build packs/hello       # Baut y5n-packs-hello-0.1.0.whl
yak update --force          # Installiert

yak shell
greet                       # → "use 'su' to login"
```

---

## Future

| Syntax | Description |
|---|---|
| `yak create app <name>` | Anwendung (eigener Prozess, anderer Host) |
| `yak create service <name>` | Hintergrunddienst |
| `yak create command <path>` | Verschachtelte Commands: `contact add` |
