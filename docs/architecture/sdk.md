# SDK

How to write packs and commands in Python.

## Two layers: SDK domains over the generic port ABI

The SDK exposes capabilities on two levels:

```
             Python SDK
                 │
     ┌───────────┼────────────┐
     ▼           ▼            ▼
  session       store       runtime      (domains: stable, typed,
     │           │            │           language-friendly API)
     └───────────┼────────────┘
                 ▼
               ports                    (generic capability API /
                 │                       escape hatch)
                 ▼
             Runtime Bus                (the ABI)
```

- **SDK domains** (`session`, `store`, `runtime`, `io`, `fs`, `scheduler`,
  `timer`, `network`, `viewport`, `security`, `resources`) are the
  **developer API**: stable, typed, domain-named. They hide transport and
  port names, inject the caller's context automatically, and return typed
  models (`await session.current().user`, `store.get("crm")`, ...).
- **`ports`** is the **generic capability API / escape hatch**. It is the
  default path for arbitrary capabilities — especially pack-provided ones
  (`ports.get("ident.auth")`, `ports.get("my.company.foo")`). A pack
  capability is not a core SDK domain.

The rule: a capability that belongs to the Yakoon execution environment is
a first-class SDK domain; everything else goes through `ports`.

A domain may be a typed facade over a port (`session` over the `session`
port, `store` over the `store` port) or an effect DSL over flow primitives
(`io`, `fs`). That wrapper is not redundant indirection — its task is the
stable, typed developer API itself.

## Context

`context` is read-only: the frozen snapshot of the current invocation.
`context.current()`, `context.request()`, `context.session()`, ... never
leave the process. Live state (session, store) is fetched through the
domains, which go over the bus.
