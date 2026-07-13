"""Build workspace/ from config.yml mounts.

Reads config.yml and creates a workspace/ directory where each
mount point is a symlink to its source.  Shallow mounts (e.g.
``root``) are expanded entry-by-entry so that deeper mounts
(e.g. ``root/opt/crm``) can overlay specific paths.
"""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.yml"
WORKSPACE_PATH = ROOT / "workspace"


def _load_config() -> dict[str, str]:
    with open(CONFIG_PATH) as f:
        raw = yaml.safe_load(f)
    mounts: dict[str, str] = {}
    for key, value in raw.get("workspace", {}).items():
        if not isinstance(value, str):
            continue
        mounts[key] = value
    return mounts


def _resolve_source(source: str) -> str:
    source = os.path.expanduser(source)
    if not os.path.isabs(source):
        source = str(ROOT / source)
    return source


def _find_overrides(mounts: dict[str, str]) -> set[str]:
    """Return entry names that should be skipped when expanding a mount."""
    expanded = {
        m for m in mounts
        if any(o != m and o.startswith(f"{m}/") for o in mounts)
    }
    overrides: set[str] = set()
    for mount_point in mounts:
        for exp in expanded:
            if mount_point.startswith(f"{exp}/"):
                rel = mount_point[len(exp) + 1:]
                first = rel.split("/")[0]
                overrides.add(first)
    return overrides


def _expand_into(
    source_dir: str,
    target_dir: str,
    skip: set[str] | None = None,
) -> None:
    """Symlink every entry from *source_dir* into *target_dir*.

    Entries whose name or sub-path appears in *skip* are omitted.
    """
    skip = skip or set()
    os.makedirs(target_dir, exist_ok=True)
    for entry in os.listdir(source_dir):
        if entry in skip:
            continue
        src = os.path.join(source_dir, entry)
        dst = os.path.join(target_dir, entry)
        os.symlink(src, dst, target_is_directory=os.path.isdir(src))


def build() -> None:
    mounts = _load_config()
    if not mounts:
        print("No mounts found in config.yml", file=sys.stderr)
        sys.exit(1)

    if WORKSPACE_PATH.exists():
        shutil.rmtree(WORKSPACE_PATH)
    WORKSPACE_PATH.mkdir(parents=True)

    # Identify shallow mounts that need entry-level expansion.
    # These are mounts whose path is a prefix of another mount.
    expanded: set[str] = set()
    for mount_point in mounts:
        if any(
            other != mount_point and other.startswith(f"{mount_point}/")
            for other in mounts
        ):
            expanded.add(mount_point)

    # Build overrides set for each expanded mount
    overrides = _find_overrides(mounts)

    for mount_point, source in sorted(mounts.items(), key=lambda x: x[0]):
        target = WORKSPACE_PATH / mount_point
        source_abs = _resolve_source(source)

        if mount_point in expanded:
            _expand_into(source_abs, str(target), skip=overrides)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(
                source_abs,
                str(target),
                target_is_directory=os.path.isdir(source_abs),
            )

    print(f"Workspace built at {WORKSPACE_PATH}")


if __name__ == "__main__":
    build()
