from __future__ import annotations

from pathlib import Path

from yak.hosts.cli.cwd import find_installation_path


def run(args, mgr) -> None:
    path = args.path or find_installation_path()
    if path is None:
        print("No installation specified. Use --path <dir> or cd into one.")
        return
    try:
        mgr.update(Path(path).resolve())
        print(f"Updated: {path}")
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
