from __future__ import annotations

from pathlib import Path

from yak.hosts.cli.cwd import find_installation_path
from yak.hosts.cli.ui import TerminalUI


def run(args, mgr) -> None:
    path = Path(args.path).resolve() if args.path else find_installation_path()
    if path is None:
        print("No installation specified. Use --path <dir> or cd into one.")
        return

    ui = TerminalUI(verbose=getattr(args, "verbose", False))
    ui.title(f'Updating "{path.name}"')

    try:
        with ui.step("Distribution"):
            inst = mgr.load(path)
            if inst is None:
                raise RuntimeError("Installation not found")
            dist = mgr._repo.resolve_distribution(inst.distribution)
            ui.detail(inst.distribution)

        with ui.step("Packs"):
            packs, mounts, tools = mgr._resolver.resolve(dist)
            ui.detail(", ".join(packs))

        with ui.step("Workspace"):
            mgr._materializer.materialize(path, dist.name, packs, mounts=mounts)

        with ui.step("Mounts"):
            for m in mounts:
                ui.detail(f"{m.pack} → {m.target}")

        with ui.step("Environment"):
            from datetime import UTC, datetime
            from yak.installation.models import Installation, InstallationStatus

            now = datetime.now(UTC)
            inst.packs = packs
            inst.status = InstallationStatus.MATERIALIZED
            inst.updated = now
            mgr._write_state(inst)
            mgr._installer.install(inst, tools=tools, sdk_path=mgr._sdk_path)
            inst.status = InstallationStatus.CREATED
            inst.updated = datetime.now(UTC)
            mgr._write_state(inst)

        ui.ok(f"{path.name} updated")

    except Exception as e:
        ui.fail(f"Update failed: {e}")
