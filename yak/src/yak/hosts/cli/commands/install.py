from __future__ import annotations

from pathlib import Path

from yak.hosts.cli.ui import TerminalUI


def run(args, mgr) -> None:
    ui = TerminalUI()
    ui.title(f'Installing "{args.target}"')

    try:
        with ui.step("Distribution"):
            dist = mgr._repo.resolve_distribution(args.target)

        with ui.step("Packs"):
            packs, mounts = mgr._resolver.resolve(dist)
            ui.detail(", ".join(packs))

        with ui.step("Workspace"):
            root = Path(args.path).resolve()
            root.mkdir(parents=True, exist_ok=True)
            mgr._materializer.materialize(root, dist.name, packs, mounts=mounts)

        with ui.step("Mounts"):
            for m in mounts:
                ui.detail(f"{m.pack} → {m.target}")

        with ui.step("Environment"):
            from datetime import UTC, datetime
            from yak.installation.models import Installation, InstallationStatus

            now = datetime.now(UTC)
            inst = Installation(
                name=args.target,
                distribution=dist.name,
                root=root,
                packs=packs,
                status=InstallationStatus.MATERIALIZED,
                created=now,
                updated=now,
            )
            mgr._write_state(inst)
            mgr._installer.install(inst, sdk_path=mgr._sdk_path)
            inst.status = InstallationStatus.CREATED
            inst.updated = datetime.now(UTC)
            mgr._write_state(inst)

        ui.ok(f"{args.target} ready at {root}")

    except Exception as e:
        ui.fail(f"Installation failed: {e}")
