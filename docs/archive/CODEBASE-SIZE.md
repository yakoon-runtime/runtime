# Codebase Size

Stand: 2026-06-07

## Overview

| Layer | Python LOC | Other (templates, css) |
|-------|-----------:|----------------------:|
| Runtime Kernel | 12 585 | 102 |
| Spaces | 5 946 | 183 |
| Apps | 848 | 188 |
| **Total** | **19 412** | **473** |

---

## Runtime Kernel

### `y5ncore-base` — 5 101 LOC

| Area | LOC |
|------|----:|
| Projection (model, percept, transfer, wire) | ~1 350 |
| Nodes (node, path, ports, handler, space) | ~900 |
| Flow (dsl, primitives, patterns, policies) | ~550 |
| Naming (key, namespace, resolver) | ~130 |
| Plugins (container, modules, ports) | ~215 |
| Capabilities (discovery, workflow) | ~280 |
| Permissions | ~70 |
| Runtime (container, input, sessions) | ~220 |
| Sources (request, source) | ~180 |
| API (dsl, nodes, ports, projections, etc.) | ~160 |
| Other (clients, transport, resources, values) | ~50 |

### `y5ncore-runtime` — 7 484 LOC

| Area | LOC |
|------|----:|
| Projection (compiler, transport, rendering, projector) | ~1 900 |
| Machine (engine, scheduler, resolver, host, runner, task) | ~1 360 |
| Wire (runtime, machine, compiler, plugins, projector) | ~570 |
| Capabilities (workflow, discovery, permission, audit) | ~1 700 |
| Sources (data, registry) | ~550 |
| Flow (cursor, flow, types) | ~160 |
| Sessions (service, session, identity) | ~380 |
| Runtime (sessions, devtools, trace, bus, error) | ~460 |
| Naming (allocator, counter, shard) | ~100 |
| Plugins (manager, registry) | ~120 |
| Transport (local) | ~35 |
| Settings | ~55 |
| Services (guidance) | ~25 |
| Other | ~60 |

---

## Spaces

### `y5nspace-ident` — 4 448 LOC

| Area | LOC |
|------|----:|
| Services (user, group, membership, permgrant, account, auth, resolver) | ~1 310 |
| Runtime (user, group, member, grant, su, whoami, setup, bootstrap) | ~2 080 |
| Models (user, group, membership, permgrant, account) | ~340 |
| Space / ports / settings | ~125 |

### `y5nspace-runtime` — 1 071 LOC

| Area | LOC |
|------|----:|
| Runtime commands (version, welcome, setup, jobs) | ~370 |
| Labs (dsl, demos, patterns) | ~490 |
| Space / ports | ~85 |

### `y5nspace-shell` — 427 LOC

| Area | LOC |
|------|----:|
| System commands (cd, ls, man, pwd) | ~285 |
| Setup / space / ports | ~145 |

---

## Apps

| App | LOC | Description |
|-----|----:|-------------|
| `y5napp-textual` | 501 | Rich TUI client |
| `y5napp-web` | 210 | Web client |
| `y5napp-ssh` | 105 | SSH server |
| `y5napp-console` | 32 | Console (debug) |

---

## Templates (SAM)

| Space | Files | LOC |
|-------|------:|----:|
| `y5nspace-ident` | 28 | 131 |
| `y5nspace-runtime` | 2 | 23 |
| `y5nspace-shell` | 11 | 139 |
| `y5ncore-runtime` | 5 | 100 |
| **Total** | **46** | **393** |

Plus `terminal.tcss` (Textual client): 188 LOC.
