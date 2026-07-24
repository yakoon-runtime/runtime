from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC, datetime
from pathlib import Path

from yak.distribution.models import PackName
from yak.installation.models import Installation, InstallationStatus
from yak.repository.artifact import ArtifactStore
from yak.repository.interface import Repository
from yak.resolver.resolver import Resolver
from yak.workspace.materializer import Materializer


class InstallationManager:
    def __init__(
        self,
        repository: Repository,
        artifact_store: ArtifactStore,
        installations_root: Path,
    ) -> None:
        self._repo = repository
        self._artifacts = artifact_store
        self._resolver = Resolver(lambda name: repository.resolve_distribution(name))
        self._materializer = Materializer(artifact_store)
        self._installations_root = installations_root

    # ── Install ──

    def install(self, target: str) -> Installation:
        dist = self._repo.resolve_distribution(target)
        if dist is None:
            raise ValueError(f"Unknown target: {target}")

        packs = self._resolver.resolve(dist)
        now = datetime.now(UTC)
        root = self._installations_root / target
        self._materializer.materialize(root, dist.name, packs)

        inst = Installation(
            name=target,
            distribution=dist.name,
            root=root,
            packs=packs,
            status=InstallationStatus.MATERIALIZED,
            created=now,
            updated=now,
        )
        self._write_state(inst)
        return inst

    # ── Update ──

    def update(self, name: str) -> Installation:
        inst = self._load(name)
        if inst is None:
            raise ValueError(f"Installation not found: {name}")

        if inst.status == InstallationStatus.RUNNING:
            raise RuntimeError(f"Cannot update running installation: {name}")

        dist = self._repo.resolve_distribution(inst.distribution)
        if dist is None:
            raise ValueError(f"Distribution not found: {inst.distribution}")

        packs = self._resolver.resolve(dist)
        now = datetime.now(UTC)
        self._materializer.materialize(inst.root, dist.name, packs)

        inst.packs = packs
        inst.updated = now
        self._write_state(inst)
        return inst

    # ── Doctor ──

    def doctor(self, name: str) -> list[str]:
        issues: list[str] = []
        inst = self._load(name)
        if inst is None:
            return ["Installation not found"]

        root = inst.root
        if not root.exists():
            issues.append("Installation root missing")

        if not (root / "workspace.toml").exists():
            issues.append("workspace.toml missing")

        if not (root / ".yak" / "state.toml").exists():
            issues.append("state.toml missing")

        for pack in inst.packs:
            if not self._artifacts.has_artifact(pack):
                issues.append(f"Pack '{pack}' not found")

        return issues

    # ── Run / Stop ──

    def run(self, name: str) -> None:
        inst = self._load(name)
        if inst is None:
            raise ValueError(f"Installation not found: {name}")

        runtime_dir = self._artifacts.get_artifact(PackName("runtime"))
        if runtime_dir is None:
            raise RuntimeError("Runtime artifact not found")

        main = runtime_dir / "boot" / "python" / "__main__.py"
        if not main.exists():
            raise RuntimeError(f"Runtime entry not found: {main}")

        subprocess.Popen(
            [sys.executable, str(main)],
            cwd=inst.root,
        )

        inst.status = InstallationStatus.RUNNING
        inst.updated = datetime.now(UTC)
        self._write_state(inst)

    def stop(self, name: str) -> None:
        inst = self._load(name)
        if inst is None:
            raise ValueError(f"Installation not found: {name}")

        import signal

        pid_file = inst.root / ".yak" / "runtime.pid"
        if pid_file.exists():
            pid = int(pid_file.read_text().strip())
            try:
                os.kill(pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            pid_file.unlink(missing_ok=True)

        inst.status = InstallationStatus.STOPPED
        inst.updated = datetime.now(UTC)
        self._write_state(inst)

    # ── Status ──

    def status(self, name: str) -> Installation | None:
        return self._load(name)

    def statuses(self) -> list[Installation]:
        if not self._installations_root.exists():
            return []
        result = []
        for entry in sorted(self._installations_root.iterdir()):
            inst = self._load(entry.name)
            if inst is not None:
                result.append(inst)
        return result

    # ── Internals ──

    def _load(self, name: str) -> Installation | None:
        state_file = self._installations_root / name / ".yak" / "state.toml"
        if not state_file.exists():
            return None
        return self._read_state(state_file)

    def _write_state(self, inst: Installation) -> None:
        state_dir = inst.root / ".yak"
        state_dir.mkdir(parents=True, exist_ok=True)
        manifest = f"""\
[installation]
name = "{inst.name}"
distribution = "{inst.distribution}"
status = "{inst.status.value}"
packs = [{", ".join(f'"{p}"' for p in inst.packs)}]
created = "{inst.created.isoformat() if inst.created else ""}"
updated = "{inst.updated.isoformat() if inst.updated else ""}"
"""
        (state_dir / "state.toml").write_text(manifest)

    def _read_state(self, path: Path) -> Installation | None:
        import tomllib

        with open(path, "rb") as f:
            data = tomllib.load(f)
        inst_data = data.get("installation", {})
        if not inst_data:
            return None
        return Installation(
            name=inst_data.get("name", ""),
            distribution=inst_data.get("distribution", ""),
            root=path.parent.parent,
            packs=[PackName(p) for p in inst_data.get("packs", [])],
            status=InstallationStatus(inst_data.get("status", "created")),
            created=self._parse_dt(inst_data.get("created")),
            updated=self._parse_dt(inst_data.get("updated")),
        )

    @staticmethod
    def _parse_dt(raw: str | None) -> datetime | None:
        if raw:
            try:
                return datetime.fromisoformat(raw)
            except ValueError:
                pass
        return None
