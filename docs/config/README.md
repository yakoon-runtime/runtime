# Configuration Templates

This directory contains templates for the runtime configuration.
To activate, copy to `~/.config/yakoon/` or point `YAKOON_CONFIG_DIR` here.

## Spaces

Per-space config lives in `spaces/<space>.yml` and is resolved by
`resolve_space_config(space)` from `~/.config/yakoon/spaces/`. Each pack
reads its own space: `crm.yml` for the CRM pack, `luma.yml` for the Luma
pack.

Both templates point the event store and sequencer at the shared space
database `yakoon_crm` (postgres).

```
cp docs/config/spaces/crm.yml  ~/.config/yakoon/spaces/crm.yml
cp docs/config/spaces/luma.yml ~/.config/yakoon/spaces/luma.yml
```

Without a space file the pack falls back to the in-memory store.

