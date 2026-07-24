from __future__ import annotations


def run(args, mgr) -> None:
    target = mgr._target.resolve(args.target)
    if target is None:
        print(f"Target not found: {args.target}")
        return
    packs = mgr._resolver.resolve(target)
    for p in packs:
        print(p)
