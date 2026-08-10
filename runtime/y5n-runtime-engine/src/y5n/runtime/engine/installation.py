"""Installation model (ADR-19): the deployment mapping materialized by `yak`.

The installation is the machine-specific product of the assembler. It maps
logical stores to physical deployments — the only place in the system that
knows databases. The runtime consumes it at startup to build its store
registry.

A logical store maps to exactly one deployment; several logical stores may
map to the same deployment (they share the physical resource, ADR-19).

```yaml
# .yak/installation/deployment.yml
stores:
  crm:
    deployment: postgres-main
  ident:
    deployment: postgres-main

deployments:
  postgres-main:
    backend: postgres
    dsn: postgresql://...
```

Secrets are never here — only references (`secret:`), resolved by the
secret store.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True, slots=True)
class Deployment:
    """A physical resource a logical store is mapped to."""

    name: str
    backend: str = "memory"
    dsn: str = ""
    secret: str | None = None


@dataclass(frozen=True, slots=True)
class StoreMapping:
    """The deployment a logical store is mapped to."""

    store: str
    deployment: str


@dataclass(frozen=True, slots=True)
class Installation:
    """The deployment mapping of one installation."""

    stores: dict[str, StoreMapping] = field(default_factory=dict)
    deployments: dict[str, Deployment] = field(default_factory=dict)

    def deployment_for(self, store: str) -> Deployment | None:
        mapping = self.stores.get(store)
        if mapping is None:
            return None
        return self.deployments.get(mapping.deployment)


def load_installation(path: Path) -> Installation | None:
    """Load an installation from a deployment file, or None when absent."""
    if not path.is_file():
        return None
    with open(path) as f:
        data = yaml.safe_load(f) or {}

    deployments: dict[str, Deployment] = {}
    for name, raw in (data.get("deployments") or {}).items():
        if not isinstance(raw, dict):
            continue
        deployments[name] = Deployment(
            name=name,
            backend=raw.get("backend", "memory"),
            dsn=raw.get("dsn", ""),
            secret=raw.get("secret"),
        )

    stores: dict[str, StoreMapping] = {}
    for store, raw in (data.get("stores") or {}).items():
        if not isinstance(raw, dict):
            continue
        deployment = raw.get("deployment")
        if isinstance(deployment, str):
            stores[store] = StoreMapping(store=store, deployment=deployment)

    return Installation(stores=stores, deployments=deployments)


def to_dict(installation: Installation) -> dict[str, Any]:
    """Serialize an installation back to a deployment dict."""
    return {
        "stores": {
            store: {"deployment": mapping.deployment}
            for store, mapping in sorted(installation.stores.items())
        },
        "deployments": {
            name: {
                k: v
                for k, v in {
                    "backend": dep.backend,
                    "dsn": dep.dsn or None,
                    "secret": dep.secret,
                }.items()
                if v is not None
            }
            for name, dep in sorted(installation.deployments.items())
        },
    }


def build_store_registry(
    installation: Installation | None,
    default_objects,
    build_store,
) -> dict[str, Any]:
    """Build the resolver's store registry from an installation.

    Each logical store maps to the physical store of its deployment.
    Several logical stores on the same deployment share one physical
    instance. Logical stores without a deployment entry resolve to the
    default object (the installation does not map everything yet).
    """
    if installation is None:
        return {}
    registry: dict[str, Any] = {}
    per_deployment: dict[str, Any] = {}
    for store, mapping in installation.stores.items():
        if mapping.deployment in per_deployment:
            registry[store] = per_deployment[mapping.deployment]
            continue
        deployment = installation.deployments.get(mapping.deployment)
        if deployment is None:
            registry[store] = default_objects
            continue
        built = build_store(deployment)
        per_deployment[mapping.deployment] = built
        registry[store] = built
    return registry
