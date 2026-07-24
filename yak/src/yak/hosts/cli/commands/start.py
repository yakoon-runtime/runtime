from __future__ import annotations

import os
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
    pid_file = path / ".yak" / "runtime.pid"

    # Check if already running
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)  # signal 0 = process check
            print(f"Runtime already running (pid {pid})")
            return
        except (ProcessLookupError, ValueError):
            pid_file.unlink(missing_ok=True)

    python = path / ".venv" / "bin" / "python"
    proc = subprocess.Popen(
        [str(python), "-m", "y5napp.runtime"],
        cwd=path,
    )
    pid_file.write_text(str(proc.pid))
    print(f"Started: {path} (pid {proc.pid})")
