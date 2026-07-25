# Yakoon Document Schema (YDS)

YDS is the wire format of the Yakoon platform.

Every component — compiler, runtime, SDK, and client — communicates
in YDS.  It is the single contract between all layers.

```
         YDF (.ydf)
             │
         Compiler
             │
         YDS (dict/JSON)
             │
    ┌───────┼───────┐
    │       │       │
 Runtime  Client  SDK
```

## Files

| File | Description |
|------|-------------|
| `yds-v1.yaml` | The canonical specification |
| `README.md`   | This file |

## Concepts

- A **Document** is a tree of **Blocks**.
- Blocks contain **Properties** (type-specific fields) and optionally
  nested child blocks.
- **Inline** nodes form rich-text content within certain block fields.
- The schema is versioned.  The version appears in the document root.

## Design principles

1. **Self-describing** — every node carries a `type` discriminator.
2. **Flat where possible** — documents are trees of uniform dicts.
3. **No runtime state in the schema** — IDs, timestamps, and
   traversal metadata are added by the Normalizer, not part of YDS.
4. **Client-agnostic** — the same document renders on web, terminal,
   or console.
