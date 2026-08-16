# Configuration Templates

This directory contains templates for the runtime configuration.
To activate, copy to `~/.config/yakoon/` or point `YAKOON_CONFIG_DIR` here.

## Spaces

Per-space config lives in `spaces/<space>.yml` and is resolved by
`resolve_space_config(space)` from `~/.config/yakoon/spaces/`. Each pack
reads its own space: `contacts.yml` for the Contacts pack, `worlds.yml` for
the Worlds pack.

Both templates point the event store and sequencer at the shared space
database `yakoon_contacts` (postgres).

```
cp docs/config/spaces/contacts.yml ~/.config/yakoon/spaces/contacts.yml
cp docs/config/spaces/worlds.yml ~/.config/yakoon/spaces/worlds.yml
```

Without a space file the pack falls back to the in-memory store.

