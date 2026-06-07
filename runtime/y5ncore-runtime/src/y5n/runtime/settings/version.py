from __future__ import annotations

import subprocess
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as pkg_version

from y5n.base.runtime.info import RuntimeInfo

PACKAGE_NAME = "y5ncore-runtime"


def resolve_runtime_info() -> RuntimeInfo:
    version = _resolve_version().lstrip("v")
    build = _resolve_build()
    return RuntimeInfo(version=version, build=build)


# ----------------------------------
# Resolution chain
# ----------------------------------


def _resolve_version() -> str:
    return (
        _from_metadata()
        or _get_git_tag()
        or _read_version_file()
        or "unknown"
    )


def _resolve_build() -> str | None:
    return _get_git_commit()


def _from_metadata() -> str | None:
    try:
        return pkg_version(PACKAGE_NAME)
    except PackageNotFoundError:
        return None


def _get_git_tag() -> str | None:
    try:
        return (
            subprocess.check_output(
                ["git", "describe", "--tags"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return None


def _get_git_commit() -> str | None:
    try:
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return None


def _read_version_file(path: str = "version.txt") -> str | None:
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return None
