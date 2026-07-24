from __future__ import annotations

from pathlib import Path


def run(args, mgr) -> None:
    try:
        path = Path(args.path).resolve() if args.path else None
        inst = mgr.install(args.target, path=path)
        print(f"Installed: {inst.name}")
        print(f"  distribution: {inst.distribution}")
        print(f"  packs: {', '.join(inst.packs)}")
        print(f"  root: {inst.root}")
    except ValueError as e:
        print(f"Error: {e}")
