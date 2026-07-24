from __future__ import annotations

from yak.hosts.cli.cwd import find_installation_from_cwd, find_installation_path


def run(args, mgr) -> None:
    # Check CWD first
    path = find_installation_path()
    if path is not None:
        inst = mgr.load(path)
        if inst is not None:
            print(inst.name)
            return

    # List all managed installations
    all_inst = mgr.statuses()
    for inst in all_inst:
        print(inst.name)
