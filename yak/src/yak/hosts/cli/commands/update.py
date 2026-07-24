from __future__ import annotations


def run(args, mgr) -> None:
    try:
        inst = mgr.update(args.name)
        print(f"Updated: {inst.name}")
        print(f"  packs: {', '.join(inst.packs)}")
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
