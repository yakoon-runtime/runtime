from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

from yak.distribution.models import PackName
from yak.distribution.target import TargetResolver
from yak.installation.models import Installation, InstallationStatus
from yak.resolver.resolver import Resolver
from yak.workspace.materializer import Materializer


class InstallationManager:
    def __init__(
        self,
        target_resolver: TargetResolver,
        packs_root: Path,
        installations_root: Path,
    ) -> None:
        self._target = target_resolver
        self._resolver = Resolver(lambda name: self._target.resolve(name))
        self._materializer = Materializer(packs_root)
        self._installations_root = installations_root

    def install(self, target: str) -> Installation:
        dist = self._target.resolve(target)
        if dist is None:
            raise ValueError(f"Unknown target: {target}")

        packs = self._resolver.resolve(dist)
        now = datetime.now(UTC)
        root = self._installations_root / target
        ws = self._materializer.materialize(root, dist.name, packs)

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

    def status(self, name: str) -> Installation | None:
        state_file = self._installations_root / name / ".yak.toml"
        if not state_file.exists():
            return None
        return self._read_state(state_file)

    def statuses(self) -> list[Installation]:
        if not self._installations_root.exists():
            return []
        result = []
        for entry in sorted(self._installations_root.iterdir()):
            state = self.status(entry.name)
            if state is not None:
                result.append(state)
        return result

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
