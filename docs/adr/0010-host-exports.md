# ADR 10: Host Exports — One Mechanism for Code and Content

**Status:** Proposed — design decisions made, implementation pending

> **A component exports capabilities. The host invokes them.**
>
> Yakoon describes a reference. The host decides how it is resolved. Scheme
> names and reference values are host-defined. The node owns the definition
> of its capabilities; the host interprets their reference expressions. As
> little architecture as possible.

A component ships code *and* content. Both are delivered the same way: the
component exports a capability, and the host invokes it. `main` is a capability
like `man`, `projection`, or `logo`. The host never knows *how* a capability is
implemented — the component decides. The host only knows how to call.

## Context

yak.yml today distinguishes two kinds of references, resolved by two different
mechanisms:

```yaml
entry:
  run: pack:y5n.packs.system.info:main

man:
  default: file:resources/man.ydf
```

Semantically, both lines mean the same thing: **"host, invoke this exported
capability."** `entry.run` says *execute*; `man.default` says *deliver*. Yet the
runtime treats them as unrelated:

| | `entry.run` | `man` / `document` |
|---|---|---|
| Semantics | "host, execute this capability" | "host, deliver this capability" |
| Mechanism | import module, call function | read a file |
| Resolution site | the host (boot) | the engine tree (build time) |
| Result | async generator of Pulses | `Path` |

The core flows already are the run contract: every component has an input
(`entry.run`), an output (the Pulse stream) and an error flow — automatically.
What a component must *declare* are its additional boundaries: `man`,
`document`, `logo`, ... — content the host delivers on demand. This ADR is about
that layer.

## Problem

1. **Two reference grammars, two resolution sites.** `pack:mod:func` (entry,
   resolved by the host) vs `file:path` / `pack:mod:path` (resource, resolved by
   the engine tree at build time, `nodes/tree.py:166-192`).
2. **Build-time module imports.** The unused `pack:` resource scheme
   (`_resolve_pack_path`, `nodes/tree.py:477`) imports modules at tree build —
   for every workspace node, regardless of use. Contradicts "the engine
   references, the host invokes."
3. **Content is assumed to be a file.** A component delivering its man page from
   a database, a web service, or an embedded string cannot express that.
4. **Only the projector consumes content.** `man`, commands, and tests should
   reach content the same way.
5. **The engine would grow a resolver registry.** Avoided: hosts own resolvers.

## Decision

### Principle

> **Yakoon describes a reference. The host decides how it is resolved.**
> **Scheme names and reference values are host-defined.**
> **The node owns the expression; the host interprets it.**
> As little architecture as possible.

Yakoon's runtime knows references: `scheme:value` strings handed to a host. It
never interprets them. Hosts register the schemes they support — names and
values are their convention:

```
Python host:   file:<path>     resource:<value>
.NET host:     file:<path>     assembly:<value>
newer host:    both
```

A reference is a contract between pack author and host — not Yakoon's concern.
This matches the port convention (`ports.get("crm.contact.service")`, never
`ports.get("contact")`).

### References, resolved by the host

A resource is declared as a **reference expression** — a `scheme:value` string
whose meaning the host defines. Every host interprets the schemes it supports;
there is no central resolver registry. `file:` is not a runtime built-in — a
host registers it for scripts, an embedded host may not. A reference's
semantics are scoped to the node's host.

### The resolve scheme: `resource:`

The PythonHost names its content references `resource:` — the host delivers a
Resource; where it comes from is the host's business:

```yaml
entry:
  run: pack:y5n.packs.system.info:main        # run contract, unchanged

man:
  default: resource:y5n.packs.system.info:man

document:
  default: resource:shared.projections:list
```

`resource:<value>` means: **"resolve this capability into a Resource."** The
value is host-defined: a module and function today, a logical component-id
later. References are fully qualified — a component may source its help,
projection, or icons from any other component:

```yaml
man:
  default: resource:company.documentation:man
```

`file:<path>` stays for scripts:

```yaml
man:
  default: file:resources/man.ydf
```

### Two contracts, one mechanism

| Section | Contract | Capability | Result |
|---------|----------|-----------|--------|
| `entry` | **run** | `main(...)` | a Flow — async generator of Pulses |
| `man` / `document` | **resolve** | `man(**params)` | a `Resource` |

The reference grammar and the invocation mechanism (import + call, host-owned)
are shared. The contract is implied by the section: `entry` expects the run
contract; `man` / `document` the resolve contract. In the value-stream view
both are streams — run is a sustained, bidirectional flow; resolve is a stream
that ends in one response.

### The Host — the interpreter of a component's expressions

A Host is the runtime environment of a component — the implementation behind
a language or execution strategy (`PythonComponentHost`, a future .NET host,
...). The seam is drawn by one question: **who owns the expression, and who
interprets it?**

| Ownership | What | Example |
|-----------|------|---------|
| **The node** | the definition of its capabilities — reference *expressions* | `man: {default: resource:man}` |
| **The host** | the interpretation of those expressions | `resource:man` → importlib, assembly, ... |
| **The runtime** | neither schemes nor their meaning | `resolve(node, "man")` |

A node's yak.yml does not hold references to resources — it holds **reference
expressions** whose meaning is host-defined. `resource:man` is a host
expression, not a resolved reference: the Python host reads it via
`importlib.resources`, a .NET host via its assembly API. The node owns the
expression; it does not know what it means.

The same seam runs through `entry.run`: it too is a node-owned expression
(`pack:y5n.packs.system.info:main`) that the host interprets. `execute` and
`resolve` are therefore the same pattern — the node declares, the host
interprets, the runtime knows nothing.

The host is a node itself (`/boot/python/runtime`), referenced by other nodes
via `host:`. The runtime needs no loading or registration — the host node is
already in the tree; the runtime delegates to it.

The host declares its interpretation in its own yak.yml:

```yaml
# /boot/python/runtime/.yak/yak.yml
resolve:
  default: pack:y5n.runtime.boot.python.runtime:resolve
```

The tree builds a `resolve` handler on the host node from this declaration —
lazy, no module import at build time. Every host node exports its own
interpretation, so arbitrary hosts run in parallel without conflicting: a
ticker host and the Python host coexist, each resolving its own nodes.

The host owns variant selection too (`de` / `en` / `default`): it reads the
expressions a node declared for a capability, picks the variant, and
interprets. The runtime never unpacks `node.resources`:

```python
def resolve(self, node, capability, parameters=None) -> Resource
```

There is no resolver registry and no global host-service registration — each
host node provides its own `resolve` handler, and the runtime knows no host
type.

### Bootstrap linking

> The runtime is allowed to resolve `pack:` only for host bootstrap
> declarations. Nothing else.

Before a host can interpret reference expressions, the first host itself must
be loaded. For this reason, the runtime performs a minimal, mechanical linking
step for the `entry.run` and `resolve` declarations of host nodes.

This is **not** reference interpretation. It is **bootstrap linking**. The
runtime does not understand what `pack:y5n.runtime.boot.python.runtime:resolve`
*means* — it only loads the declared function so the first host can run. All
subsequent reference expressions (`resources:`, `ports:`, a command's
`entry.run`) are interpreted exclusively by the host.

There are therefore exactly two kinds of references:

| Kind | Where | Who resolves it |
|------|-------|-----------------|
| **Bootstrap references** | `entry:` / `resolve:` of a *host node* | the runtime's single bootstrap linker (`pack:` only) |
| **Runtime references** | `resources:`, `ports:`, a *command's* `entry.run` | the host |

The rule is deliberately narrow: the bootstrap linker understands one scheme
(`pack:<module>:<func>`), one meaning (load the function), and is exercised
only for host nodes that have no host of their own. The first host cannot be
interpreted by anything but the runtime — every later reference can.

### The `Resource` result

A resolve capability returns a `Resource` with exactly two requirements:

```python
resource.read_text()  # str
resource.read_bytes() # bytes
```

Internal carriers (`TextResource`, `PathResource`, `TraversableResource`,
`EmbeddedResource`, `HttpResource`, ...) are implementation details. The
signature stays stable across YDF, SVG, PNG, PDF, Markdown. A resolve capability
is a plain function:

```python
def man() -> Resource:
    return Resource.traversable(files(__package__) / "resources" / "man.ydf")
```

### One service: `runtime.resource`

Every consumer reaches content through the same service — the projector, the
`man` command, other commands, tests:

```python
resource = await runtime.resolve(node=info, capability="man")
text = resource.read_text()
```

The service has two operations:

```python
resolve(node, capability, parameters) -> Resource
supports(node, capability)            -> bool
```

`man` is no special case. The service **dispatches per node-host**: it finds
the target node, follows its `host:` path, and delegates to the host node's
`resolve` handler. The runtime never knows which host it is — exactly as
`session` and `flows` hide theirs. Because the interpretation is a capability
of the host node (not a globally registered service), parallel hosts each
resolve their own nodes. For v1, `entry` (the run contract) stays on its
existing path; resolve is the new delegation.

### Resolution is lazy and host-owned

- The engine tree stores raw reference expressions — no resolution, no module
  import at build time.
- The host interprets a node's expressions on demand, through the node's host.
- Consumers reach content only through `runtime.resource`.

## Rejected alternatives

- **Relative capability references** — implies content lives in the entry
  module. Rejected: too much architecture.
- **Module anchor inheritance** — implicit resolution. Rejected: explicit
  everywhere.
- **A resolver registry (host-path → resolver)** — the runtime would know every
  host type (`PythonHostResolver`, `DotnetHostResolver`, ...). This is the
  executor trap the platform already avoided: the runtime enumerates
  implementations. Rejected: the node owns expressions, the host interprets
  them.
- **Host-registered global services** (`document`, `projection`, `resource`
  registered by each host at init) — the bus holds one adapter per port;
  parallel hosts would overwrite each other. Rejected: the interpretation is a
  capability of the host node, dispatched per node-host.
- **`file:` as a runtime built-in** — rejected: it is a host scheme like any
  other.
- **`pack:` as the capability scheme** — merges the host's namespace into the
  scheme name. Rejected.
- **`export:` as the capability scheme** — describes the provider, not what the
  host returns. Rejected in favor of `resource:`.
- **`runtime.host` as the service** — exposes the host; consumers want
  resources. Rejected in favor of `runtime.resource`.
- **Mini-languages for parameters** — rejected: yak.yml is the grammar;
  parameters are YAML.

## Consequences

### What disappears

| Today | Tomorrow |
|-------|----------|
| `pack:<mod>:<path>` resource refs (unused) | `resource:<value>` — capability resolution |
| Prefix-free resource strings as file paths | gone (references carry a scheme) |
| Resource resolution at tree build | lazy resolution via `runtime.resource` |
| `node.resources: dict[str, dict[str, Path]]` | reference expressions |
| `_resolve_pack_path` (engine) | gone |

### What stays

- `entry` — the run contract, unchanged (`pack:mod:func`).
- `file:` — a PythonHost-registered scheme for scripts.
- The `man` command, document adapter, and projector keep their consumer roles;
  they now share one resolution path.

### Benefits

- **One mechanism for code and content** — host-owned, reference-based.
- **Self-contained, freely composed components** — content may live in any
  component, local or remote.
- **No build-time imports.**
- **Components decide** — database, web, filesystem, or embedded string.
- **`man` is no special case** — every consumer uses the same service.
- **The host stays fully hidden** behind `runtime.resource`, like `session` and
  `flows`.

### Trade-offs

- Fully qualified references repeat the component per entry.
- A resolve capability adds one function per resource.
- `node.resources` and `system:nodes` adapt from paths to references.

### Open questions

1. **Component identity.** The `<value>` part is today the Python module. A
   logical component-id (`resource:crm.contacts:man`) needs no architecture
   change — only the host's resolution becomes smarter.
2. **Run contract over the bus.** v1 keeps `entry` on its existing path. Later,
   `invoke` may join `resolve` on the service.
3. **Caching.** Resolve handlers are pure functions of (ref, parameters) —
   cache results per session?
4. **Resource surface.** `read_text()` / `read_bytes()` suffice for v1; a
   `data` / `raw` surface may follow.
