# Entry references

Reference schemes used in `yak.yml` entry declarations (`entry.run`,
`entry.setup`), resource references (`resource:` fields) and resolver
expressions.

## Reference schemes

| Scheme | Meaning |
|--------|---------|
| `cap:` | Component entry |
| `file:` | File entry |
| `resource:` | Resource reference |

> **Schemes identify the kind of reference. Hosts define how host-specific
> entry payloads are interpreted.**

The scheme never describes an implementation technology. The
declarative tree must not know whether a component is implemented in
Python, .NET or anything else — that is what `host:` declares.

## `cap:` — Component entry

```yaml
host: /boot/python/runtime
entry:
  run: cap:y5n.caps.worlds.apps.exit.list:main
```

`cap:` identifies an entry provided by an installed component. The
entry syntax following the scheme is defined by the selected host.

The payload is opaque to the tree — it is linked, not interpreted (ADR-10).
The host owns the contract behind `cap:`.

Python host:

```text
cap:y5n.caps.worlds.apps.exit.list:main
    └──────────────────────┬──────┘
                    module:callable
```

A .NET host would define its own payload syntax:

```yaml
host: /boot/dotnet/runtime
entry:
  run: cap:Yakoon.Caps.Worlds.Exit.List:Run
```

The scheme stays the same — only the payload differs, and the host
interprets it.

Note: `cap:` is not short for "capability". The `y5n.caps.worlds...`
namespace and the `cap:` scheme are different levels:

```text
cap:                    Reference type
y5n.caps.worlds...      Python namespace
```

## `file:` — File entry

```yaml
entry:
  run: file:some/path/foo.py
```

`file:` resolves a file-based executable entry. The path is resolved
relative to the workspace root.

## `resource:` — Resource reference

```text
resource:y5n.caps.worlds.resources.loader:content
```

`resource:` resolves content through the resource system (projections,
manuals, …). It is used in resource reference fields, not in
`entry.run`.