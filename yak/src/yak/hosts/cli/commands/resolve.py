from __future__ import annotations


def run(args, mgr) -> None:
    dist = mgr._repo.resolve_distribution(args.target)
    if dist is None:
        print(f"Target not found: {args.target}")
        return
    packs, mounts = mgr._resolver.resolve(dist)
    for p in packs:
        print(p)
    if mounts:
        print()
        print("Mounts:")
        for m in mounts:
            print(f"  {m.pack} → {m.target}")
