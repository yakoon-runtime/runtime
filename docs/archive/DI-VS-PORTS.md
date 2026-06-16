# Why Yakoon Ports? — What DI Alone Doesn't Solve

## Dependency Injection vs. Yakoon Ports

---

## 1. Two Directions Instead of One

Dependency Injection is **top-down**: the container has everything, consumers pull from it.

```python
# DI: only one direction
container.bind(Db, postgres)
handler = Handler(db=container.get(Db))
```

Yakoon needs **two directions**:

```python
# ↓ Delegate downward (who you are determines what you can do)
root.ports.provide(OnSourceRead, ds.read)

# ↑ Export upward (plugin says: "I can do this")
space.ports.publish(Namespaces, my_namespace_service)
```

A space like `y5nspace-ident` must not only *receive* things, but also *offer* things — exposing its identity services to the parent node.

In DI, the parent node would need to know in advance which services the child offers, wiring everything manually. Yakoon enables **self-organizing exports** — a space says: "I'm initialized, here are my capabilities for you above."

---

## 2. Authority Is Bound to Position, Not Type

In DI, a service gets what it needs because it declares it (`@inject`). Position in the system is irrelevant.

In Yakoon, **position in the tree** determines what you can see:

```
Root (OnProjectionResolve, OnSourceRead, OnCompile, ...)
  └─ system (sees everything from Root)
      └─ ls (sees everything from system + Root)
  └─ runtime (sees everything from Root)
      └─ version (sees everything from runtime + Root, but NOT system/ls)
```

A deep node in the `ident` space cannot simply use `OnSourceRead` from the Root space — it must be in the subtree mounted under Root. **Authority is inherited through hierarchy position, not through import declarations.**

An `@inject` decorator gives no context about *where* in the system this code runs. Yakoon says: "You are Node X under Parent Y — so you have access to Z, but not to W."

---

## 3. Subtree Autonomy (Composition without Coordination)

DI requires central coordination: somewhere a `WireModule()`, `AppModule` or `CompositionRoot` must know **all** dependencies.

```python
# DI: central coordination
class AppModule:
    def configure(self, container):
        container.bind(Projector, ...)
        container.bind(Store, ...)
        container.bind(UserService, ...)  # Root must know about Ident service!
        container.bind(GroupService, ...) # Root must know about Ident service!
```

Yakoon allows **independently developed subtrees** that self-configure:

```python
# Space wiring (independently developed in y5nspace-ident)
async def setup(space):
    store = EntityStore(...)
    space.ports.provide(UserService, UserService(store))
    space.ports.provide(Namespaces, Namespaces())

# Root wiring (coordinates only mounting, no detail knowledge)
platform.mount(shell_space)
platform.mount(ident_space)    # doesn't know what ident does internally
platform.mount(runtime_space)  # doesn't know what runtime does internally
```

The Root doesn't need to know what `y5nspace-ident` needs or offers internally. It mounts the space, and the space organizes itself. **This is roughly equivalent to loading a Linux module — it registers itself without the kernel wiring every function individually.**

---

## 4. Capability Security (What You Don't Have, You Can't Call)

DI solves the problem "how do I get my dependencies?" — but not the problem "how do I prevent unauthorized code from accessing sensitive services?"

A classic DI framework gives you either:

- **Global container** → anyone can get anything (Ambient Authority)
- **Scoped container** → but scope boundaries are orthogonal to business logic

Yakoon has a **built-in authorization mechanism** with `PermissionChecker` and hierarchical visibility:

```python
# node.py: Position determines visibility
class Node:
    ports: NodePorts       # my capabilities
    parent: Node | None    # my context in the tree
    children: dict[str, Node]  # my sub-nodes
```

- A node in `runtime/labs` sees different capabilities than a node in `ident/admin`
- Even if code calls `ports.get()`, the capability is only found if the container chain provides it
- `fork()` and `mount()` draw explicit boundaries

DI frameworks (Guice, Spring, Castle Windsor, etc.) give you either everything or nothing — they have no concept of **capability scopes bound to tree position**. A service in Spring gets its dependencies regardless of *where* in the request graph it is called.

---

## 5. No Central Dependency Wire Orgy

In classic DI systems, the `WireModule` / `AppModule` / `CompositionRoot` grows with every new component. Everything must be known centrally.

```python
# Typical DI composition root (grows with every feature)
wire = [
    Projector, Compiler, Normalizer,
    UserService, GroupService, MembershipService,
    PermissionService, AuditService, DiscoveryService,
    ShellService, RuntimeService, WelcomeService,
    EntityStore, MemoryBackend, PostgresBackend,
    ...
]
```

Yakoon distributes wiring across spaces:

```python
# runtime.py (Root wiring) — only 9 lines of binding
platform.ports.provide(OnSourceRead, ds.read)
platform.ports.provide(OnSessionSave, session_manager.save)
platform.ports.provide(OnAuthorizeRead, perm_checker.can_read)
platform.ports.provide(OnAuthorizeWrite, perm_checker.can_write)
platform.ports.provide(OnProjectionResolve, projector.project)
platform.ports.provide(OnResourceLoad, package_reader.get_text)
platform.ports.provide(OnJinjaRender, jinja_engine.render_str)
platform.ports.provide(OnCompile, compiler.compile)
platform.ports.provide(OnErrorResolve, error_resolve)

# shell/setup.py (Space wiring) — completely independent
space.ports.provide(OnManualResolve, manual_resolver)

# ident/setup.py (Space wiring) — completely independent
space.ports.provide(UserService, UserService(store))
space.ports.provide(GroupService, GroupService(store))
space.ports.publish(OnAuthenticate, authenticator.authenticate)
```

**Each space is its own composition root.** The Root doesn't need to know that the Shell space needs an `OnManualResolve` or that `y5nspace-ident` offers a `UserService`. The space handles itself.

---

## 6. Dynamic Plugin Architecture

DI systems are usually **statically configured at startup**. You say: "These 5 modules are wired."

Yakoon allows **dynamic loading of subtrees**:

```python
# A space can mount a subtree at runtime
shell_node.mount(new_space)

# Or provide capabilities after the fact
node.ports.provide(NewService, my_service)
```

Because `fork()` establishes a parent chain, new nodes automatically see existing capabilities. The new subtree doesn't need to be added to central wiring — it is simply attached.

---

## Summary

| Problem | Dependency Injection | Yakoon Ports |
|---------|-------------------|--------------|
| **Direction** | Top-down only | `provide` ↓ + `publish` ↑ |
| **Authority** | Declared (`@inject`) | Position in tree |
| **Subtree Autonomy** | Central coordination required | Self-wiring spaces |
| **Access Control** | All or nothing | Hierarchical, graduated |
| **Composition** | Everything known at root | Decentralized wiring |
| **Dynamics** | Mostly static at startup | Runtime mounting possible |
| **Plugins** | Must be registered at root | Self-registering |
| **Metaphor** | "Here are your dependencies" | "Here is what you are authorized for" |
