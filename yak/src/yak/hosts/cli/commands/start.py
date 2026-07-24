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
    # Determine port from config
    import tomllib

    port = 9100
    config = path / "yakoon-runtime.yml"
    if config.exists():
        try:
            import yaml

            cfg = yaml.safe_load(config.read_text()) or {}
            port = cfg.get("listen", {}).get("port", 9100)
        except Exception:
            pass

    wrapper = path / ".venv" / "bin" / "yakoon-runtime"
    if not wrapper.exists():
        wrapper.write_text(
            "#!/usr/bin/env python3\n"
            "import ctypes, ctypes.util, sys\n"
            "libc = ctypes.CDLL(ctypes.util.find_library('c'))\n"
            "name = f'yakoon:{sys.argv[1]}'\n"
            "libc.prctl(15, name.encode(), 0, 0, 0)\n"
            "sys.argv[0] = name\n"
            "sys.argv.pop(1)\n"
            "from y5napp.runtime.__main__ import main\n"
            "main()\n"
        )
        wrapper.chmod(0o755)

    proc = subprocess.Popen([str(wrapper), str(port)], cwd=path)
    pid_file.write_text(str(proc.pid))
    print(f"Started: {path} (pid {proc.pid})")
