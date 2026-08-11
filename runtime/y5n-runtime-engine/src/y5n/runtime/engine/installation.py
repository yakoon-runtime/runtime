"""Installation model (ADR-19): binding logical capabilities to physical backends.

The installation is the machine-specific product of the assembler. It
binds each logical store to a physical backend — the only place in the
system that knows how to reach a database.

```yaml
# .yak/installation/deployment.yml
stores:
  crm:
    backend: postgresql://db.internal:5432/crm
    credentials: env://CRM_DATABASE

  telemetry:
    backend: memory://
```

Two URIs per store, both interpreted by their scheme:

- ``backend`` (required) — the non-secret physical binding. The scheme
  selects the store adapter (`postgresql://`, `memory://`, `http://`).
- ``credentials`` (optional) — the source of secret connection
  information. The scheme selects the credential resolver (`env://`,
  later `vault://`, `file://`, ...).

There is no named registry: no `deployments:`, no `instance:` — a store
is bound directly. Unsupported credential schemes raise explicitly; there
is no fallback and no implicit default.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


class UnsupportedCredentialsScheme(RuntimeError):
    """Raised when a credentials URI uses a scheme no resolver provides."""


@dataclass(frozen=True, slots=True)
class StoreBinding:
    """The binding of one logical store to a physical backend."""

    store: str
    backend: str
    credentials: str | None = None


@dataclass(frozen=True, slots=True)
class Installation:
    """The bindings of one installation."""

    stores: dict[str, StoreBinding] = field(default_factory=dict)

    def binding_for(self, store: str) -> StoreBinding | None:
        return self.stores.get(store)


def load_installation(path: Path) -> Installation | None:
    """Load an installation from a deployment file, or None when absent."""
    if not path.is_file():
        return None
    with open(path) as f:
        data = yaml.safe_load(f) or {}

    stores: dict[str, StoreBinding] = {}
    for store, raw in (data.get("stores") or {}).items():
        if not isinstance(raw, dict):
            continue
        backend = raw.get("backend")
        if not isinstance(backend, str):
            continue
        credentials = raw.get("credentials")
        stores[store] = StoreBinding(
            store=store,
            backend=backend,
            credentials=credentials if isinstance(credentials, str) else None,
        )

    return Installation(stores=stores)


def to_dict(installation: Installation) -> dict[str, Any]:
    """Serialize an installation back to a deployment dict."""
    return {
        "stores": {
            store: {
                k: v
                for k, v in {
                    "backend": binding.backend,
                    "credentials": binding.credentials,
                }.items()
                if v is not None
            }
            for store, binding in sorted(installation.stores.items())
        },
    }


def build_store_registry(
    installation: Installation | None,
    build_store,
) -> dict[str, Any]:
    """Build the resolver's store registry from an installation.

    Each logical store is bound to the physical store of its backend URI.
    Two stores with the same backend URI share one physical instance.
    """
    if installation is None:
        return {}
    registry: dict[str, Any] = {}
    per_backend: dict[str, Any] = {}
    for store, binding in installation.stores.items():
        if binding.backend in per_backend:
            registry[store] = per_backend[binding.backend]
            continue
        built = build_store(binding)
        per_backend[binding.backend] = built
        registry[store] = built
    return registry
