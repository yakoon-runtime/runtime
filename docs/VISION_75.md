# Yakoon Vision

> *A semantic namespace runtime — from commands to capabilities.*

---

## Status Quo: Version 75

Today, Yakoon is a **command platform**. Its core abstractions are:

| Concept | Role |
|---------|------|
| `Node` | A navigable or executable element in a tree |
| `Space` | A Python package that contributes one root node |
| `Resolver` | Traverses the tree, resolves invocations |
| `Projection` | Renders node output for a client (terminal, web) |

A command is a Python class. A Space is a Python package. The tree lives in RAM. The developer writes:

```python
class MyCommand(Node):
    key = "my-command"
    resolvable = True
    navigable = False
```

This model works. It gave us a stable language, a deterministic resolver, and multiple projection targets. But it carries inherited constraints:

- **One node per Space** — the package name becomes the tree name
- **Static tree** — nodes are defined at import time, not discovered at runtime
- **Python-only** — every capability must be a Python class
- **RAM-only** — the namespace has no persistence

---

## The Insight: Node Was Never the Goal

The Node was an experiment. It allowed us to stabilise the language — `resolvable`, `navigable`, `contextual`, `?`, usage signatures — before asking the deeper question:

> **What is the deployment unit? And why must it differ from the runtime unit?**

The Node model answers: *a Python class in a package installed via pip.*

But the emerging answer is: **a folder on disk.**

---

## Target: Version 80 — The Capability Model

```
Folder
    ↓
Capability Compiler
    ↓
Node (internal)
    ↓
Resolver
    ↓
Projection
```

In this model, the developer never writes a `Node` class. They create a **folder**:

```
my-command/
    capability.yaml     # metadata: name, permissions, resolver
    run/                # executable implementations
        python.py
        bash.sh
        wasm
    templates/          # projection templates (terminal, web, ...)
    assets/             # static files (icons, PDFs, images)
    manuals/            # documentation
    tests/              # validation
```

The folder IS the capability. Copy it into the runtime path, and it appears in the namespace. Delete it, and it vanishes.

### Capability Compiler

The runtime scans capability folders and **compiles** them into internal Node objects:

```text
my-command/
    capability.yaml
    run/python.py
    templates/usage.yak
    manuals/man.yak
```

↓

```python
Node(
    key="my-command",
    resolvable=True,
    navigable=False,
    executor=PythonExecutor("my-command/run/python.py"),
    templates={...},
    manuals={...},
)
```

The Node is no longer the API. It is the **internal representation** — the bytecode of the namespace.

---

## Contributions Instead of Spaces

A Python package no longer declares one root node. It declares **contributions** — mounts at arbitrary paths:

```python
class PlatformContribution:
    def contributions(self):
        return [
            Mount("/var",    VarCapability()),
            Mount("/usr",    UsrCapability()),
            Mount("/home",   HomeProvider()),
            Mount("/system", SystemCapability()),
            Mount("/luma",   LumaCapability()),
        ]
```

Or equivalently, a folder tree:

```
capabilities/
    var/
    usr/
    home/
    system/
    luma/
```

is scanned and mounted automatically.

### Key Properties

- **The package name disappears from the namespace.** `y5nspace-shell` does not mount under `/shell`. It mounts whatever it contributes wherever it belongs.
- **Multiple mounts per package.** A single package can contribute to `/var`, `/usr`, `/home`, `/system` — because those are logical domains, not packaging concerns.
- **Arbitrary depth.** Contributions are not limited to root: `Mount("/identity/users")` and `Mount("/luma/models")` are equally valid.

---

## Providers: Dynamic Namespace

Not all nodes are static folders. Some produce children at runtime:

```python
class HomeProvider(Node):
    def children(self):
        user = context.current_user
        for name in self.store.list_user_nodes(user):
            yield UserNode(name, self.store)

class DatabaseProvider(Node):
    def children(self):
        return [TableNode(t) for t in Database.tables()]

class FilesystemProvider(Node):
    def __init__(self, root: Path):
        self.root = root

    def resolve(self, segments):
        target = self.root / "/".join(segments)
        if target.is_dir():
            return FsMirrorDir(target)
        if target.is_file():
            return FsMirrorFile(target)
        return None
```

These are not different kinds of nodes. They are **Nodes with a provider** — a strategy that answers `children()` or `resolve()` at call time.

The runtime sees no difference:

```
/home           → HomeProvider (database-backed)
/mnt/projects   → FilesystemProvider (OS-backed)
/crm/customers  → DatabaseProvider (SQL-backed)
/shell          → StaticCapability  (folder-backed)
```

All are just **nodes** in the same namespace.

---

## Projection as the Universal Consumer

The namespace has no intrinsic UI. It is consumed through **projections**:

| Projection | Renders | Example |
|------------|---------|---------|
| Terminal | ANSI text | `ls`, `cd`, `man` |
| Web | HTML/DOM | Browser-based namespace browser |
| REST | JSON | `GET /api/namespace/shell/info` |
| Voice | Speech | "Show me info about the shell" |
| AI | Context | Agent traverses namespace for tool selection |

A capability folder supplies templates for each projection:

```
my-command/
    templates/
        terminal.yak    # ANSI rendering
        web.html        # HTML rendering
        json.schema     # JSON response schema
        ai.prompt       # AI system prompt fragment
```

The runtime selects the template matching the active projection. The capability author writes once; the runtime projects everywhere.

---

## Yakoon Becomes Invisible

When the deployment unit is a folder and the namespace is compiled from contributions and providers, Yakoon recedes from the user's awareness:

```
Developer:  cp -r ./my-app /usr/share/yakoon/capabilities/
Admin:      mount git /org/services  (mirrors a Git repo into the namespace)
User:       yakoon cd /services/my-app/info
Browser:    http://yakoon.local/crm/customer/4711
```

The same namespace — accessed through different projections, powered by the same capabilities.

---

## The Inversion

| Today | Vision |
|-------|--------|
| `pip install y5nspace-shell` | `cp -r ./shell /usr/share/yakoon/capabilities/` |
| `Node(key="info", run=info)` | `info/run/python.py` exists on disk |
| `space.root_node = shell` | `ShellContribution.mounts()` returns paths |
| Tree built at import time | Namespace compiled at startup |
| Children are lists | Children come from providers |
| Python is the only runtime | Any executor (bash, wasm, node, ...) |
| One node per package | Many contributions per package |
| Package name = tree name | Package name is irrelevant |

---

## Migration Path

This is not a rewrite. It is a layered evolution:

1. **Contributions interface** — add `Space.contributions()` alongside existing `root_node`. Both are valid. New packages use contributions.

2. **Folder scanner** — add a `FolderCapability` that reads `capability.yaml` from a directory tree and produces nodes. This is a provider like any other.

3. **Provider API** — formalise `children()` and `resolve()` as the provider contract. Existing static nodes implement the default (return `self._children`).

4. **Multi-executor** — add `Executor` abstraction. `PythonExecutor` wraps the current `run()` call. `BashExecutor`, `WasmExecutor`, `NodeExecutor` follow.

5. **Projection templates** — allow capabilities to supply per-projection templates. Start with optional, not required.

Each step is backwards-compatible. Today's `Node(...)` classes continue to work. New capabilities can use any or all of the new mechanisms.

---

## Architectural Principles (Updated)

| Principle | Statement |
|-----------|-----------|
| **Namespace first** | The namespace is the primary artifact. Everything else is derived. |
| **Folder as unit** | A folder is the deployment, versioning, and runtime unit. |
| **Compiled namespace** | The namespace is assembled at startup from contributions, not defined in code. |
| **Provider abstraction** | Static nodes, databases, filesystems, and Git repos all implement the same Node interface. |
| **Projection neutrality** | The namespace has no intrinsic UI. All output is a projection. |
| **Capability over Node** | The capability (folder + metadata) is the authoring unit. The Node is internal. |

---

## What This Enables

- **Zero-deploy commands**: drop a folder into the capabilities directory, and it is immediately available.
- **Multi-language runtimes**: a capability folder can contain `run/python.py`, `run/bash.sh`, and `run/wasm` — the runtime chooses by availability.
- **User-owned namespace**: `~/yakoon/capabilities/` is writable by the user. They create, edit, and delete capabilities without admin rights.
- **Filesystem mirroring**: `mount fs /home/user/projects` maps a real directory into the namespace. `ls`, `cd`, `cat` work transparently.
- **Distributed namespace**: contributions come from local folders, Git repos, network mounts, and database queries — all in one tree.
- **Company-wide capability distribution**: a DevOps team maintains a Git repo of capability folders. CI/CD syncs it to the runtime. No package registry needed.

---

## The Analogy

Yakoon's evolution mirrors the Unix kernel's relationship with filesystems.

Unix does not know what a filesystem is. It knows the VFS interface — `read`, `write`, `open`, `readdir`. EXT4, tmpfs, procfs, NFS, FUSE all implement the same interface. The kernel does not care where data lives.

Yakoon does not know what a capability is. It knows the Node interface — `children`, `resolve`, `run`. Folders, databases, Git repos, REST APIs, and AI agents all implement the same interface. The runtime does not care how a node produces its output.

This is the next abstraction level: **not a command platform, but a namespace runtime** — where every tool, every data source, every service is a node in one semantic tree, accessible from any projection, deployable as a folder.

---

*Draft — July 2026. Evolved from the Node model (v75) toward the Capability model (v80).*
