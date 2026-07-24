from __future__ import annotations


def run(args, mgr) -> None:
    try:
        mgr.stop(args.name)
        print(f"Stopped: {args.name}")
    except (ValueError, RuntimeError) as e:
        print(f"Error: {e}")
