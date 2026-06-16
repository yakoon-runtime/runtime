# Ports Mechanism in Yakoon

## Overview

The Ports system is a **pure dependency injection framework** based on hierarchical containers — without a framework, without decorators, without magic. It allows capabilities (functions, services) to be passed through the node tree so that each node gets exactly what it needs.

---

## Building Block: `Container`

**File:** `runtime/y5ncore-base/src/y5n/base/runtime/container.py`

Every `Container` is a simple key-value store with two special features:

1. **Parent chain**: A container has a `parent`. If a port is not found, the parent container is consulted → **hierarchical lookup**.
2. **Static or lazy**: You can bind ready instances (`bind()`) or factories (`bind_lazy()`) — lazy is executed on first access and cached.

```python
container = Container(allow_override=True)
container.bind(MyPort, my_instance)        # static
container.bind_lazy(MyPort, factory_fn)    # lazy
container.get(MyPort)                      # → my_instance
```

**Methods:**

| Method | Description |
|---------|-------------|
| `bind(port, capability)` | Registers a ready capability instance |
| `bind_lazy(port, factory)` | Registers an async factory (executed on first `get()`) |
| `get(port)` | Fetches capability from own container → parent → ... → Root |
| `contains(port)` | Checks if port exists anywhere in the chain |
| `fork()` | Creates child container with itself as parent |
| `mount(root)` | Attaches container chain to new root (extends lookup) |

---

## `NodePorts` — The Two Directions

**File:** `runtime/y5ncore-base/src/y5n/base/nodes/ports.py`

`NodePorts` encapsulates **two** containers:

```python
class NodePorts:
    _publish_to: Container  # upward (visible to parent)
    _local: Container       # local + downward (children inherit)
```

**API:**

| Method | Effect |
|---------|--------|
| `provide(port, capability)` | Registers in `_local` → visible to this node **and all child nodes** |
| `publish(port, capability)` | Registers in `_publish_to` → visible **to the parent node** |
| `get(port)` | Searches `_local` → parent container → ... → Root |
| `has(port)` | Checks if port exists in the local chain |
| `fork()` | Creates child `NodePorts` (see inheritance) |
| `mount(parent)` | Attaches into parent tree (see mounting) |

---

## Inheritance Chain: `fork()` and `mount()`

### `fork()` — Child Node Inherits Capabilities

Called in `Node.add()` (`node.py:216-217`):

```python
if self.ports:
    child.ports = self.ports.fork()
```

`fork()` creates new `NodePorts`:

```python
def fork(self) -> NodePorts:
    return NodePorts(
        publish_to=self._local,    # child publishes into parent's local
        local=self._local.fork(),  # child's local has parent's local as parent
    )
```

**Effect:** Children see all capabilities of the parent node, but can add or override their own (if `allow_override=True`).

### `mount()` — Attaching Subtrees

Called in `Node.mount()` and in Runtime wiring:

```python
def mount(self, parent: NodePorts) -> None:
    self._local.mount(parent._local)   # extend lookup into parent tree
    self._publish_to = parent._local   # publications go to parent's local
```

**Effect:** The mounted tree keeps its internal hierarchy but extends its lookup into the parent tree. Publications go directly into the parent's local container.

---

## The Wiring Process

**File:** `runtime/y5ncore-runtime/src/y5n/runtime/wire/runtime.py:146-154`

All platform services are registered as ports on the **Root node**:

```python
platform.ports.provide(OnSourceRead, ds.read)
platform.ports.provide(OnSessionSave, session_manager.save)
platform.ports.provide(OnAuthorizeRead, perm_checker.can_read)
platform.ports.provide(OnAuthorizeWrite, perm_checker.can_write)
platform.ports.provide(OnProjectionResolve, projector.project)
platform.ports.provide(OnResourceLoad, package_reader.get_text)
platform.ports.provide(OnJinjaRender, jinja_engine.render_str)
platform.ports.provide(OnCompile, compiler.compile)
platform.ports.provide(OnErrorResolve, error_resolve)
```

Then all `Nodes` (spaces) are attached via `platform.mount(node)` → **every node automatically sees all platform ports through the hierarchy lookup**.

---

## Consumption in Nodes

Every command handler receives `space: NodeSpace`. Required services are fetched via `space.ports.get(PortType)`:

### Simple Example: `version` Command

**File:** `spaces/y5nspace-runtime/src/y5nspace/runtime/runtime/version.py`

```python
async def run(space: NodeSpace):
    projection = await space.ports.get(OnProject)(
        name="version/list",
        lang=space.session.lang,
        state={...},
    )
    yield out(projection)
```

The handler only needs the projection function. It was registered by Runtime wiring as `OnProjectionResolve` on Root — the node sees it through the port hierarchy.

### Complex Example: `su` Command

**File:** `spaces/y5nspace-ident/src/y5nspace/ident/runtime/su.py`

```python
async def run(space: NodeSpace):
    namespaces = space.ports.get(Namespaces)
    resolver = space.ports.get(PermissionResolver)
    on_authenticate = space.ports.get(OnAuthenticate)
    on_save_session = space.ports.get(OnSessionSave)
    on_project = space.ports.get(OnProject)
    ...
```

Here multiple ports are needed simultaneously:
- `Namespaces` → provided by the Ident space itself (`provide`)
- `OnAuthenticate` → provided by the Ident space
- `OnSessionSave` → provided by Runtime wiring on Root
- `OnProject` → provided by Runtime wiring on Root
- `PermissionResolver` → provided by the Ident space

---

## Ports as Protocols

Ports are **protocols** (not concrete types) — this enables loose coupling:

```python
# spaces/y5nspace-ident/src/y5nspace/ident/ports.py
class OnProject(Protocol):
    async def __call__(
        self, *, name: str, lang: str, state: dict
    ) -> Projection: ...
```

Binding is purely **structural** — the registered function only needs to match the protocol. **No registration decorator, no magic, no interface registry.** `Container.bind()` only checks if it's an instance (not a class), but not the type.

---

## Summary

| Concept | Meaning |
|---------|---------|
| `Container` | Hierarchical DI container with parent chain |
| `NodePorts` | Encapsulates two containers: local (inherited downward) + publish (upward) |
| `provide(port, cap)` | Makes capability available locally + to children |
| `publish(port, cap)` | Exports capability to parent node |
| `get(port)` | Fetches capability from local chain (node → parent → ... → Root) |
| `fork()` | Creates child scope: child sees everything from parent, can add its own |
| `mount(parent)` | Attaches complete subtree, extends lookup into parent tree |
| `On*` protocols | Typed port definitions as `Protocol` classes (structural typing) |

### Data Flow Diagram

```
Root Node (Platform)
  _local: [OnProjectionResolve, OnSourceRead, OnSessionSave, ...]
  |
  mount() → Ident Space
  |   _local: [Namespaces, UserService, GroupService, ...]
  |   _local.parent → Root._local  (sees platform ports)
  |   |
  |   add() → "su" Node
  |       _local: []  (empty, but inherited from Ident Space)
  |       _local.parent → Ident Space._local
  |       _local.parent.parent → Root._local
  |
  mount() → Shell Space
      _local: [...]
      _local.parent → Root._local
```

A `get(OnProject)` in the `su` node traverses:
1. `su Node._local` → not found
2. `Ident Space._local` → not found
3. `Root._local` → **found** (registered there via `provide`)

---

## Capability System vs. Dependency Injection

The implementation uses DI mechanics (`Container.bind/get`, parent chain). The **design** is a Capability System.

### What Makes It a Capability System

**1. Two directions (`provide` vs `publish`)**

Real DI only knows a container with consumers pulling from it. `NodePorts` has two explicit directions:

```python
def provide(self, port, capability):
    self._local.bind(port, capability)  # ↓ delegates downward (for children)

def publish(self, port, capability):
    self._publish_to.bind(port, capability)  # ↑ exports upward (for parent)
```

`provide` **delegates authority** downward — a node consciously gives a capability to children.
`publish` **exports authority** upward — a node makes something accessible to its parent.
This is no longer pure dependency supply, but **explicit authority transfer with direction**.

**2. `fork()` creates authority boundaries, not just scopes**

```python
def fork(self) -> NodePorts:
    return NodePorts(
        publish_to=self._local,    # child publishes into parent local
        local=self._local.fork(),  # child sees parent local as parent
    )
```

Every `fork()` draws a boundary: the child can see parent capabilities via lookup, but `publish()` writes specifically into the parent container. It's not about convenience, but about **who is allowed to export what where**. In DI this would be simply `child = parent.fork()` — flat, without direction.

**3. `mount()` establishes trust zones**

```python
def mount(self, parent: NodePorts) -> None:
    self._local.mount(parent._local)    # extend lookup
    self._publish_to = parent._local    # redirect publications
```

A mounted subtree (e.g. `y5nspace-ident`) keeps its internal authority structure but gets lookup access to the parent tree. **The subtree remains autonomous** — it decides which internal capabilities it exports upward via `publish()`. This is the **Principle of Least Authority** (POLA).

**4. No global container, no ambient authority**

In classic DI there's usually a root container with ambient authority: *every* service is available *everywhere*. Yakoon does have a root, but:
- Not all ports are registered on Root — many are deep in spaces (`Namespaces`, `UserService`, `GroupService`)
- A node in the `ident` space sees Root ports (projection, sourceRead), but not the internal ports of the `runtime` space
- **Visibility is a matter of hierarchy position, not registration**

### Conceptual Differences

| Aspect | Dependency Injection | Capability System |
|--------|-------------------|-------------------|
| **Core question** | "What does this code need?" | "What is this code allowed to do?" |
| **Authority** | Ambient (everything in container is available) | Transferred (explicitly passed) |
| **Direction** | Mostly top-down or central | Explicit: provide ↓, publish ↑ |
| **Granularity** | Whole services | Individual authorized operations |
| **Boundaries** | Logical package boundaries (import) | Hierarchical authority boundaries (fork/mount) |
| **Security** | Retroactive (auth checks in methods) | Built-in (what you don't have, you can't call) |
| **Metaphor** | "Get what you need" | "Here is exactly what you are authorized for" |

### Conclusion

DI is the **How** (the technical implementation with `Container.bind/get`).
Capabilities are the **What** (the architectural concept).

`NodePorts` doesn't answer the DI question "how do I get my dependencies?" but the Capability question **"which operations is this tree node allowed to execute and who does it pass them to?"** That is the difference between a DI framework and a Capability System.
