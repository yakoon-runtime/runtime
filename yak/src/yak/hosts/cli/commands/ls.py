from __future__ import annotations


def run(args, mgr) -> None:
    all_inst = mgr.statuses()
    if not all_inst:
        return
    for inst in all_inst:
        print(inst.name)
