"""Installation model (ADR-19): every store is materialized by a StoreFactory.

The installation is the machine-specific product of the assembler. It
binds each logical store — including the runtime's own infrastructure
store ``runtime`` — to a ``StoreFactory`` import path and an opaque
config:

```yaml
# .yak/installation/deployment.yml
stores:
  runtime:
    factory: y5n.runtime.store.event.wire:EventStoreFactory
    config:
      backend: memory

  crm:
    factory: y5n.runtime.store.event.wire:EventStoreFactory
    config:
      backend: memory
```

The runtime knows no backend schemes and no credential schemes. It loads
the factory by import path and asks ``factory.build(config)`` for the
complete ``StoreRuntime``. The factory owns its config language — where a
DSN comes from (env, vault, ...) is storage knowledge, not runtime
knowledge.

``runtime`` is the reserved store of the runtime's own infrastructure
(session, activity). It is never a *default*: the resolver never falls
back to it, and no pack reaches it without declaring it — the
declaration *is* the permission.
"""

from __future__ import annotations

import importlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml

if TYPE_CHECKING:
    from y5n.runtime.store.event.runtime import StoreRuntime


RUNTIME_STORE = "runtime"
"""The reserved store name of the runtime's own infrastructure."""


@dataclass(frozen=True, slots=True)
class StoreBinding:
    """The binding of one logical store to a store factory + config."""

    store: str
    factory: str
    config: Any | None = None


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
        factory = raw.get("factory")
        if not isinstance(factory, str):
            continue
        stores[store] = StoreBinding(
            store=store,
            factory=factory,
            config=raw.get("config"),
        )

    return Installation(stores=stores)


def to_dict(installation: Installation) -> dict[str, Any]:
    """Serialize an installation back to a deployment dict.

    Insertion order is preserved: the assembler controls the order in the
    file (the `runtime` store first, then the pack stores).
    """
    return {
        "stores": {
            store: {
                k: v
                for k, v in {
                    "factory": binding.factory,
                    "config": binding.config,
                }.items()
                if v is not None
            }
            for store, binding in installation.stores.items()
        },
    }


def load_store_factory(factory: str):
    """Resolve a ``module:attr`` factory path to a callable/class."""
    module_path, sep, attr = factory.partition(":")
    if not sep or not module_path or not attr:
        raise RuntimeError(f"Invalid store factory path: {factory!r}")
    try:
        module = importlib.import_module(module_path)
        return getattr(module, attr)
    except (ImportError, AttributeError) as exc:
        raise RuntimeError(f"Cannot load store factory: {factory!r}") from exc


def build_store_registry(
    installation: Installation | None,
) -> dict[str, StoreRuntime]:
    """Build the store registry from an installation.

    Each logical store is materialized through its ``StoreFactory``. Two
    stores with the same factory and config share one physical instance.
    """
    if installation is None:
        return {}
    registry: dict[str, StoreRuntime] = {}
    per_target: dict[tuple[str, str], StoreRuntime] = {}
    for store, binding in installation.stores.items():
        target = (binding.factory, repr(binding.config))
        if target in per_target:
            registry[store] = per_target[target]
            continue
        factory = load_store_factory(binding.factory)
        built = factory.build(binding.config)
        per_target[target] = built
        registry[store] = built
    return registry
