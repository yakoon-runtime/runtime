# Yakoon CRM

*A customer relationship management bundle for Yakoon.*

CRM provides customer-facing nodes and workflows within the Yakoon
runtime tree. It is designed to be mounted into a workspace under
`/opt/crm`.

## Structure

```
src/
├── .yak/              — Bundle metadata
└── customer/          — Customer node
    ├── .yak/
    │   └── yak.yml
    └── .yak/run/      — Customer commands
```

## Mounting

Add to `workspace.yml`:

```yaml
workspace:
  /opt/crm: repos/yakoon-crm/src
```

## Built on Yakoon

CRM is implemented as a Yakoon bundle. It extends the node tree
with domain-specific nodes and commands, following the same
patterns — nodes, flows, ports, projections — as every other
Yakoon space.
