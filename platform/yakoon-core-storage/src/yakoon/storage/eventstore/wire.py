from .runtime import StoreRuntime
from .wires import wire_memory, wire_postgres


def build_store(config: dict | None = None) -> StoreRuntime:
    if not config or config.get("store") == "memory":
        return wire_memory.build_store()
    else:
        dns = config["dns"]
        return wire_postgres.build_store(dns)
