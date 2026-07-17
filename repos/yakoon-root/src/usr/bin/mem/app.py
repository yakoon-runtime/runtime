from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.ports import PROJECT


def _read_proc(path: str) -> dict[str, int]:
    result: dict[str, int] = {}
    with open(path) as f:
        for line in f:
            parts = line.split(":")
            if len(parts) == 2:
                key = parts[0].strip()
                raw = parts[1].strip().split()
                try:
                    result[key] = int(raw[0]) * 1024 if len(raw) > 1 and raw[1] == "kB" else int(raw[0])
                except (ValueError, IndexError):
                    pass
    return result


def _format_bytes(b: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PiB"


async def run(space: NodeSpace):
    proc_status = _read_proc("/proc/self/status")
    meminfo = _read_proc("/proc/meminfo")

    rss = proc_status.get("VmRSS", 0)
    vms = proc_status.get("VmSize", 0)
    total = meminfo.get("MemTotal", 0)
    available = meminfo.get("MemAvailable", 0)
    system_percent = round((total - available) / total * 100, 1) if total else 0.0

    projection = await space.ports.get(PROJECT)(
        space=space,
        state={
            "rss": _format_bytes(rss),
            "vms": _format_bytes(vms),
            "system_percent": system_percent,
            "available": _format_bytes(available),
        },
    )
    yield out(projection)
