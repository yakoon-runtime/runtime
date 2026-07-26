#!/usr/bin/env python3
"""Yakoon developer helper — start runtime and shell.

Reads yak.yml to determine which environment to use.

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
PROJECT = ROOT / "yak.yml"


def _load_project():
    if PROJECT.exists():
        return yaml.safe_load(PROJECT.read_text()) or {}
    return {}


def _resolve_env_file():
    cfg = _load_project()
    bs = cfg.get("bootstrap", {})
    env = bs.get("environment", "dev")
    art_rel = bs.get("artifacts", "apps/y5n-apps-yak/artifacts")
    return (ROOT / art_rel).resolve() / f"{env}.yml"


def main():
    env_file = _resolve_env_file()

    want_runtime = len(sys.argv) <= 1 or "runtime" in sys.argv
    want_shell = len(sys.argv) <= 1 or "shell" in sys.argv

    # Copy environment → runtime config so the runtime finds its workspace
    runtime_config = ROOT / "yakoon-runtime.yml"
    if env_file.exists() and not runtime_config.exists():
        shutil.copy2(env_file, runtime_config)
        print(f"  Config: {env_file.name} → {runtime_config.name}")

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
