from __future__ import annotations


def run(args, mgr) -> None:
    try:
        mgr.run(args.name)
        print(f"Started: {args.name}")
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
