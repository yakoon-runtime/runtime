# Node Setup Lifecycle

## Problem

A space's `setup()` may block indefinitely (e.g., waiting for a Postgres
connection that never comes). The runtime currently shows "ready" as soon
as the scheduler starts, even though space setup flows are still running
or stuck.

This breaks the contract: the runtime claims to be operational, but
a specific space never registers its ports → commands fail with
`Capability not registered for port`.

## Proposed solution

1. **Setup timeout** — the scheduler enforces a timeout (e.g. 10 s)
   per setup flow. If exceeded, the flow is aborted and the node is
   marked as `setup_failed: true` in its meta.

2. **Status query** — `system:nodes --by-key /crm` should expose
   `setup_failed` and `last_setup_error` so operators can diagnose
   degraded spaces without grepping logs.

3. **Retry mechanism** — a retry command (e.g. `crm/setup` or
   `system:setup /crm`) re-runs the failed setup for a specific node.

## Non-goals

- The runtime must **not** wait for all spaces to finish setup before
  accepting user commands. A single broken space must not block the
  whole system.

- Out-of-scope for now: dependency ordering between spaces (e.g.
  "ident must be ready before crm").
