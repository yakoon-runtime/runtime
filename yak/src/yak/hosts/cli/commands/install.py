from __future__ import annotations


def run(args, mgr) -> None:
    try:
        inst = mgr.install(args.target)
        print(f"Installed: {inst.name}")
        print(f"  distribution: {inst.distribution}")
        print(f"  packs: {', '.join(inst.packs)}")
        print(f"  root: {inst.root}")
    except ValueError as e:
        print(f"Error: {e}")
