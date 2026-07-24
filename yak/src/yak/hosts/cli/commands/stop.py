from __future__ import annotations

from yak.hosts.cli.cwd import find_installation_from_cwd


def run(args, mgr) -> None:
    name = args.name or find_installation_from_cwd()
    if not name:
        print("Error: no installation specified and not in an installation directory")
        return
    try:
        mgr.stop(name)
        print(f"Stopped: {name}")
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
