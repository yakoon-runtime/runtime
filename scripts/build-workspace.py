"""Build workspace from a workspace definition.

Reads ``workspace/<name>/workspace.yml`` and creates the tree
inside the same directory.  Mount points use ``/`` as the root
(e.g. ``/``, ``/opt/crm``) — the leading slash is stripped to
produce relative paths inside the workspace directory.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent


def _workspace_path(name: str) -> Path:
    return ROOT / "workspace" / name


def _normalise(mount_point: str) -> str:
    """Strip leading ``/`` from a mount point."""
    return mount_point.lstrip("/")


def _load_config(name: str) -> tuple[dict[str, str], Path]:
    ws_path = _workspace_path(name)
    config_path = ws_path / "workspace.yml"
    if not config_path.exists():
        print(f"Workspace definition not found: {config_path}", file=sys.stderr)
        sys.exit(1)
    with open(config_path) as f:
        raw = yaml.safe_load(f)
    mounts: dict[str, str] = {}
    for key, value in raw.get("workspace", {}).items():
        if not isinstance(value, str):
            continue
        mounts[key] = value
    return mounts, ws_path


def _resolve_source(source: str) -> str:
    source = os.path.expanduser(source)
    if not os.path.isabs(source):
        source = str(ROOT / source)
    return source


def _expand_into(
    source_dir: str,
    target_dir: str,
    skip: set[str] | None = None,
) -> None:
    """Symlink every entry from *source_dir* into *target_dir*.

    Entries whose name appears in *skip* are omitted.
    """
    skip = skip or set()
    os.makedirs(target_dir, exist_ok=True)
    for entry in os.listdir(source_dir):
        if entry in skip:
            continue
        src = os.path.join(source_dir, entry)
        dst = os.path.join(target_dir, entry)
        os.symlink(src, dst, target_is_directory=os.path.isdir(src))


def build(name: str) -> None:
    raw_mounts, ws_path = _load_config(name)
    if not raw_mounts:
        print("No mounts found in workspace.yml", file=sys.stderr)
        sys.exit(1)

    # Normalise keys: strip leading "/" so "" is root, "opt/crm" is a child.
    mounts = {_normalise(k): v for k, v in raw_mounts.items()}

    if ws_path.exists():
        for entry in ws_path.iterdir():
            if entry.name == "workspace.yml":
                continue
            if entry.is_dir() and not entry.is_symlink():
                shutil.rmtree(entry)
            else:
                entry.unlink()
    else:
        ws_path.mkdir(parents=True)

    def _has_children(key: str) -> bool:
        if key == "":
            return any(k != "" for k in mounts)
        prefix = f"{key}/"
        return any(k != key and k.startswith(prefix) for k in mounts)

    expanded = {k for k in mounts if _has_children(k)}

    overrides: set[str] = set()
    for key in mounts:
        for exp in expanded:
            if exp == "":
                first = key.split("/")[0]
                if first:
                    overrides.add(first)
            elif key.startswith(f"{exp}/"):
                rel = key[len(exp) + 1 :]
                first = rel.split("/")[0]
                overrides.add(first)

    for key, source in sorted(mounts.items(), key=lambda x: x[0]):
        target = ws_path / key if key else ws_path
        source_abs = _resolve_source(source)

        if key in expanded:
            _expand_into(source_abs, str(target), skip=overrides)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(
                source_abs,
                str(target),
                target_is_directory=os.path.isdir(source_abs),
            )

    print(f"Workspace '{name}' built at {ws_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build a Yakoon workspace")
    parser.add_argument(
        "--workspace",
        "-w",
        default="dev",
        help="Workspace name (default: dev)",
    )
    args = parser.parse_args()
    build(args.workspace)
