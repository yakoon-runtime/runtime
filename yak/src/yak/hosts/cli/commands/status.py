from __future__ import annotations

from yak.hosts.cli.cwd import find_installation_path


def run(args, mgr) -> None:
    name = args.name
    if not name:
        # Try CWD auto-detection
        path = find_installation_path()
        if path is not None:
            inst = mgr.load(path)
            if inst is not None:
                _show(inst)
                return
        # List all
        all_inst = mgr.statuses()
        if not all_inst:
            print("No installations")
            return
        for inst in all_inst:
            _show(inst)
            print()
        return

    inst = mgr.status(name)
    if inst is None:
        print(f"Installation not found: {name}")
        return
    _show(inst)


def _show(inst) -> None:
    print(f"  {inst.name}")
    print(f"    distribution: {inst.distribution}")
    print(f"    status: {inst.status.value}")
    print(f"    packs: {', '.join(inst.packs)}")
