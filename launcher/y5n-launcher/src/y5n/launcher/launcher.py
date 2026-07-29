"""y5n-launcher — ensure y5n-apps-yak is installed, then forward all arguments."""

from __future__ import annotations

import json
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path
from urllib.request import urlopen

VERSION = "0.0.2"


def _config_path() -> Path:
    return Path(__file__).resolve().parent / "launcher.yml"


def _load_config() -> dict:
    import yaml
    return yaml.safe_load(_config_path().read_text()) or {}


def _ensure_venv(context_root: Path) -> Path:
    venv = context_root / ".venv"
    python = venv / "bin" / "python"
    if not python.exists():
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv)],
            check=True, capture_output=True,
        )
    return python


def _is_installed(python: Path) -> bool:
    result = subprocess.run(
        [str(python), "-c", "import y5n.apps.yak"],
        capture_output=True,
    )
    return result.returncode == 0


def _ensure_application(python: Path, config: dict) -> None:
    """Download and install the default application from the first repository."""
    repos = config.get("repositories", [])
    app = config.get("default_application", {})
    if not repos or not app:
        return

    repo = repos[0]
    name = app["name"]

    # Fetch latest release from GitHub API
    gh_repo = repo.removeprefix("github:")
    url = f"https://api.github.com/repos/{gh_repo}/releases/latest"
    with urlopen(url) as resp:
        release = json.loads(resp.read().decode())

    # Find the artifact asset
    asset_name = f"{name}.artifact.tar.gz"
    asset_url = None
    for asset in release.get("assets", []):
        if asset["name"] == asset_name:
            asset_url = asset["browser_download_url"]
            break

    if asset_url is None:
        print(f"y5n-launcher: artifact {asset_name} not found in latest release")
        sys.exit(1)

    # Download and extract
    with urlopen(asset_url) as resp:
        data = resp.read()

    with tempfile.TemporaryDirectory() as tmp:
        tarpath = Path(tmp) / "artifact.tar.gz"
        tarpath.write_bytes(data)
        with tarfile.open(tarpath, "r:gz") as tar:
            tar.extractall(path=tmp)

        # Find and install the wheel
        for wheel in Path(tmp).rglob("*.whl"):
            subprocess.run(
                [str(python), "-m", "pip", "install", str(wheel)],
                capture_output=True, check=True,
            )
            return


def main() -> None:
    config = _load_config()
    app = config.get("default_application", {}).get("name", "y5n-apps-yak")

    if not sys.argv[1:]:
        print(f"y5n-launcher {VERSION}")
        print(f"Default application: {app}")
        print()
        print("Usage: yak <command> [options]")
        return

    if sys.argv[1] in ("-V", "--version"):
        print(f"y5n-launcher {VERSION}")
        return

    # Find or create context root
    cwd = Path.cwd()
    context_root = cwd
    for parent in [cwd, *cwd.parents]:
        if (parent / ".yak").exists():
            context_root = parent
            break

    # Ensure venv
    python = _ensure_venv(context_root)

    # Ensure default application is installed
    if not _is_installed(python):
        _ensure_application(python, config)

    # Forward all arguments to y5n-apps-yak
    result = subprocess.run(
        [str(python), "-m", "y5n.apps.yak.hosts.cli.main"] + sys.argv[1:],
        cwd=context_root,
    )
    sys.exit(result.returncode)
