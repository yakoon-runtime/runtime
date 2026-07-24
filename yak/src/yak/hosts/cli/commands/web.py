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
    result = subprocess.run(
        [str(python), "-c", "import y5napp.web; print('ok')"],
        capture_output=True, text=True,
    )
    if result.returncode != 0:
        print("Web interface not installed.")
        print("Update the installation: yak update --path", path)
        return

    subprocess.run([str(python), "-m", "y5napp.web"], cwd=path)
