"""Provision a store from the installation environment.

Bootstrap/ops entrypoint, invoked from the installation's venv:

    python -m y5n.runtime.engine.provision <module:attr> <config-json>

It loads a store factory by import path exactly like the runtime does
(``load_store_factory`` → instantiate if needed), then runs
``await factory.provision(config)``. Success exits 0; any failure
propagates unchanged as a non-zero exit.

Ownership: the engine owns the generic factory mechanics; the concrete
store (``EventStoreFactory``) owns its provision() knowledge. This module
carries no PostgreSQL/asyncpg knowledge.
"""

from __future__ import annotations

import asyncio
import json
import sys
from typing import Any

from .installation import load_store_factory


async def _run(factory_path: str, config: Any) -> None:
    factory = load_store_factory(factory_path)
    if isinstance(factory, type):
        factory = factory()
    await factory.provision(config)


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 2:
        print(
            "usage: python -m y5n.runtime.engine.provision "
            "<module:attr> <config-json>",
            file=sys.stderr,
        )
        return 2
    factory_path, raw_config = args
    try:
        config = json.loads(raw_config)
    except json.JSONDecodeError as exc:
        print(f"provision: invalid config JSON: {exc}", file=sys.stderr)
        return 2
    asyncio.run(_run(factory_path, config))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
