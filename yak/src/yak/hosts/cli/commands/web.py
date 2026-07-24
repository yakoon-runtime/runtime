from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from yak.hosts.cli.cwd import find_installation_path


def run(args, mgr) -> None:
    path = Path(args.path).resolve() if args.path else find_installation_path()
    if path is None:
        print("No installation specified. Use --path <dir> or cd into one.")
        return

    python = path / ".venv" / "bin" / "python"
    subprocess.run([str(python), "-m", "y5napp.web"], cwd=path)
