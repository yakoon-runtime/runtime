from __future__ import annotations


def run(args, mgr) -> None:
    if args.name:
        inst = mgr.status(args.name)
        if inst is None:
            print(f"Installation not found: {args.name}")
            return
        _show(inst)
    else:
        all_inst = mgr.statuses()
        if not all_inst:
            print("No installations")
            return
        for inst in all_inst:
            _show(inst)
            print()


def _show(inst) -> None:
    print(f"  {inst.name}")
    print(f"    distribution: {inst.distribution}")
    print(f"    status: {inst.status.value}")
    print(f"    packs: {', '.join(inst.packs)}")
