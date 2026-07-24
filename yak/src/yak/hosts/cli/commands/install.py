from __future__ import annotations

from pathlib import Path

from yak.hosts.cli.ui import TerminalUI


def run(args, mgr) -> None:
    ui = TerminalUI()
    ui.title(f'Installing "{args.target}"')

    try:
        with ui.step("Resolving distribution"):
            dist = mgr._repo.resolve_distribution(args.target)
            if dist is None:
                raise ValueError(f"Unknown target: {args.target}")
            ui.detail(dist.name)

        with ui.step("Resolving packs"):
            packs, mounts = mgr._resolver.resolve(dist)
            for p in packs:
                ui.detail(f"  {p}")

        with ui.step("Creating workspace"):
            root = Path(args.path).resolve() if args.path else mgr._installations_root / args.target
            root.mkdir(parents=True, exist_ok=True)
            mgr._materializer.materialize(root, dist.name, packs, mounts=mounts)

        with ui.step("Mounting packs"):
            for m in mounts:
                ui.detail(f"  {m.pack} → {m.target}")

        with ui.step("Setting up Python environment"):
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

        with ui.step("Finalizing"):
            ui.detail(f"Installation: {args.target}")
            ui.detail(f"Location: {root}")

        ui.ok("Installation completed")

    except Exception as e:
        ui.fail(f"Installation failed: {e}")
