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
    # Create a wrapper script so the process shows as 'yakoon-runtime'
    wrapper = path / ".venv" / "bin" / "yakoon-runtime"
    if not wrapper.exists():
        wrapper.write_text(
            "#!/usr/bin/env python3\n"
            "import ctypes, ctypes.util, sys\n"
            "libc = ctypes.CDLL(ctypes.util.find_library('c'))\n"
            "libc.prctl(15, b'yakoon-runtime', 0, 0, 0)  # PR_SET_NAME\n"
            "sys.argv[0] = 'yakoon-runtime'\n"
            "from y5napp.runtime.__main__ import main\n"
            "main()\n"
        )
        wrapper.chmod(0o755)

    proc = subprocess.Popen([str(wrapper)], cwd=path)
    pid_file.write_text(str(proc.pid))
    print(f"Started: {path} (pid {proc.pid})")
