# y5n-runtime-boot — The Hosts

> **What is a Yakoon Host?**

Yakoon consists of four architectural roles:

| Role | Responsibility |
|------|----------------|
| **Node** | describes itself (in `.yak/yak.yml`) |
| **Pack** | provides shared implementation and resource strategies |
| **Host** | interprets the node description |
| **Runtime** | coordinates execution |

**This project implements the Host.**

## The lifecycle

```
Runtime
    │
loads .yak
    │
Node
    │
host:
    ▼
Host
    ├── run()       → starts a flow
    └── resolve()   → delivers content
```

This is the whole story: the runtime reads a node's description, follows the
node's `host:` reference, and the host starts the node. Everything else in this
document details those two steps.

## Ownership First

Yakoon assigns every responsibility to exactly one owner.

```
Node      → describes itself
Pack      → provides shared implementation
Host      → interprets
Runtime   → coordinates
```

```
              describes
      ┌────────────────────┐
      │        Node        │
      └─────────┬──────────┘
                │
     interpreted by
                │
                ▼
      ┌────────────────────┐
      │        Host        │
      ├────────────────────┤
      │ execute            │
      │ resolve            │
      └─────────┬──────────┘
                │
     coordinated by
                │
                ▼
      ┌────────────────────┐
      │      Runtime       │
      └────────────────────┘
```

- The runtime never interprets a node.
- The host never coordinates execution.
- The pack never schedules flows.

```
When a responsibility has exactly one owner,
the implementation becomes simple.

When it does not,
the design is unfinished.
```

## What the Runtime never does

The runtime never

- imports component modules,
- interprets resource references,
- understands language-specific schemes,
- decides how a component behaves.

Those responsibilities belong to the host. This is what makes a new language
host a local change: nothing in the runtime, SDK, or structure changes.

## The Host — two twin capabilities

**Every host exposes exactly two fundamental capabilities.**

| Execute | Resolve |
|---------|---------|
| `entry.run` | `resources.ref` |
| starts a flow | delivers content |
| produces a **Flow** | produces a **Resource** |

Both take the node as their operand. The node declares, the host interprets.

## The host nodes

A host is an **ordinary node** in the structure tree — declared exactly like a
command:

```
structure/
  python/runtime/.yak/yak.yml       # the Python Runtime Host
  python/thread/.yak/yak.yml        # Python Thread Host (placeholder)
  dotnet/process/.yak/yak.yml       # .NET Process Host (not yet supported)
  process/.yak/yak.yml              # generic Process Host (placeholder)
```

A node references its host by path: `host: /boot/python/runtime`. The path
resolves to the host node; the runtime delegates to it and never knows which
host it is.

*Python Host example* — the Python Runtime Host declares both capabilities in
its own `.yak`:

```yaml
# structure/python/runtime/.yak/yak.yml
entry:
  run: pack:y5n.runtime.boot.python.runtime:run
resolve:
  default: pack:y5n.runtime.boot.python.runtime:resolve
```

Because a host is itself a component, **a new host is a new component with
execute and resolve capabilities** — nothing in the runtime changes.

## How a command runs

The runtime coordinates:

```
Runtime ── node.run(space) ──► host node ──► host.run(modified_space)
                                                    │
                          reads the node's .yak (entry.run)
                                                    │
                          resolves the entry reference
                                                    │
                          starts the node as a flow
                                                    │
                          yields Pulses upstream to the engine
```

The host *starts the node*: it turns the node's description (`.yak`) into a
running flow. The engine schedules the pulses; the host only bridges the node's
code to the runtime.

*Python Host example* — the entry reference is
`pack:y5n.packs.system.info:main`. The host imports the module, installs the
SDK context (node, session, cwd, user, flow), and runs `main()` as an async
generator — the flow — stepping it directly and yielding every `Pulse`
upstream.

## How content resolves

Content (man pages, projections) is delivered the same way — through the host.
A node declares its content under `resources:`:

```yaml
resources:
  ref: resource:y5n.packs.system.resources.loader:content
  man:
    default:
      path: info/man.ydf
  document:
    default:
      path: info/default.ydf
```

The `ref` is the pack's **resource strategy**; `man`/`document` are the
component's content **capabilities** as data. The runtime's
`runtime.resource` service dispatches to the node's host:

```
runtime.resource.resolve(node, "man")
        │
   node ── host: /boot/python/runtime ──► host.resolve(node, "man", params)
        │
   reads node.resources:  ref + capability variants
        │
   picks the variant, merges parameters
        │
   interprets the ref expression  →  Resource
```

The host calls the pack's loader with
`content(capability=..., variant=..., path=...)`. The loader decides freely
(file, database, HTTP, embedded) — Yakoon is agnostic.

## Reference expressions

A reference expression is a **declaration**. The runtime never interprets it —
it only forwards it to the node's host. It describes **what** should be used,
never **how** it is obtained.

| Scheme | Meaning | Example |
|--------|---------|---------|
| `pack:<module>:<func>` | a capability in a component | `pack:y5n.packs.system.info:main` |
| `file:<path>` | a structure-relative file | `file:app.py` |
| `resource:<module>:<func>` | a content capability | `resource:y5n.packs.system.resources.loader:content` |

Scheme names and values are **host-defined** (ADR-10). What a reference means
is a contract between the pack author and the host — not the runtime's
concern.

## A host is just another component

A host lives by the same rules as every other component. It declares itself in
`.yak`, it owns its capabilities, and it is referenced by path. There is
nothing magical about it — which is exactly why adding a new runtime
environment is a local change.

> **A host is just another component.**

To add a new host:

1. Add a host node.
2. Implement execute and resolve.
3. Point components to the new host.
