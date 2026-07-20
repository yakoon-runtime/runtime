import gc

from y5n.sdk import ports, runtime


def _read_proc(path: str) -> dict[str, int]:
    result: dict[str, int] = {}
    with open(path) as f:
        for line in f:
            parts = line.split(":")
            if len(parts) == 2:
                key = parts[0].strip()
                raw = parts[1].strip().split()
                try:
                    result[key] = (
                        int(raw[0]) * 1024
                        if len(raw) > 1 and raw[1] == "kB"
                        else int(raw[0])
                    )
                except (ValueError, IndexError):
                    pass
    return result


def _format_bytes(b: float) -> str:
    for unit in ("B", "KiB", "MiB", "GiB", "TiB"):
        if b < 1024:
            return f"{b:.1f} {unit}"
        b /= 1024
    return f"{b:.1f} PiB"


async def main():
    gc.collect()
    proc_status = _read_proc("/proc/self/status")
    meminfo = _read_proc("/proc/meminfo")

    rss = proc_status.get("VmRSS", 0)
    vms = proc_status.get("VmSize", 0)
    total = meminfo.get("MemTotal", 0)
    available = meminfo.get("MemAvailable", 0)
    system_percent = round((total - available) / total * 100, 1) if total else 0.0

    doc = ports.get("document")
    result = await doc.render(
        state={
            "rss": _format_bytes(rss),
            "vms": _format_bytes(vms),
            "system_percent": system_percent,
            "available": _format_bytes(available),
        },
    )
    await runtime.io.write(result)
