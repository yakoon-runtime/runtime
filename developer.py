#!/usr/bin/env python3
"""Yakoon developer helper — start runtime and shell.

Usage:
    python developer.py              # Start both
    python developer.py runtime      # Runtime only
    python developer.py shell        # Shell only
"""

import subprocess
import sys
import shutil
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent


def _find_yak_yml():
    """Find yak.yml: repo root takes precedence over bundled."""
    repo_yml = ROOT / "yak.yml"
    if repo_yml.exists():
        return repo_yml
    bundled = ROOT / "apps" / "y5n-apps-yak" / "yak.yml"
    if bundled.exists():
        return bundled
    return None


def _resolve_env_file():
    yml = _find_yak_yml()
    if yml is None:
        print("Error: no yak.yml found")
        sys.exit(1)

    cfg = yaml.safe_load(yml.read_text())
    bs = cfg.get("bootstrap", {})
    env = bs.get("environment", "dev")

    yml_dir = yml.parent
    art_rel = bs.get("artifacts", "apps/y5n-apps-yak/artifacts")
    artifacts_dir = (yml_dir / art_rel).resolve()
    return artifacts_dir / f"{env}.yml"


def main():
    env_file = _resolve_env_file()

    want_runtime = len(sys.argv) <= 1 or "runtime" in sys.argv
    want_shell = len(sys.argv) <= 1 or "shell" in sys.argv

    runtime_config = ROOT / "yakoon-runtime.yml"
    if env_file.exists() and not runtime_config.exists():
        shutil.copy2(env_file, runtime_config)
        print(f"  Config: {env_file.name}")

    runtime_proc = None
    if want_runtime:
        print("  Runtime: starting ...")
        runtime_proc = subprocess.Popen(
            [sys.executable, "-m", "y5n.apps.runtime"],
            cwd=ROOT,
        )

    if want_shell:
        print("  Shell:   starting ...")
        subprocess.run(
            [sys.executable, "-m", "y5n.apps.shell"],
            cwd=ROOT,
        )

    if runtime_proc:
        runtime_proc.terminate()


if __name__ == "__main__":
    main()
