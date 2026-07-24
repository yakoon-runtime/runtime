from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from yak.hosts.cli.cwd import find_installation_path


def run(args, mgr) -> None:
    path = args.path or find_installation_path()
    if path is None:
        print("No installation specified. Use --path <dir> or cd into one.")
        return

    path = Path(path).resolve()
    python = path / ".venv" / "bin" / "python"
    proc = subprocess.Popen(
        [str(python), "-m", "y5n.runtime.boot.python.runtime"],
        cwd=path,
    )
    path.joinpath(".yak", "runtime.pid").write_text(str(proc.pid))
    print(f"Started: {path} (pid {proc.pid})")
