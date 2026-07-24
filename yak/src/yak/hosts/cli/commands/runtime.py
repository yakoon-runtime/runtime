from __future__ import annotations

import os
import signal
import subprocess
import sys
from pathlib import Path

from yak.hosts.cli.cwd import find_installation_path


def run(args, mgr) -> None:
    path = _resolve_path(args)
    if path is None:
        return

    match args.action:
        case "start":
            _start(path)
        case "stop":
            _stop(path)
        case "status":
            _status(path)
        case "restart":
            _stop(path)
            _start(path)


def _resolve_path(args) -> Path | None:
    path = Path(args.path).resolve() if args.path else find_installation_path()
    if path is None:
        print("No installation specified. Use --path <dir> or cd into one.")
    return path


def _start(path: Path) -> None:
    pid_file = path / ".yak" / "runtime.pid"

    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            print(f"Runtime already running (pid {pid})")
            return
        except (ProcessLookupError, ValueError):
            pid_file.unlink(missing_ok=True)

    # Determine port from config
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

    python = path / ".venv" / "bin" / "python"
    proc = subprocess.Popen([str(wrapper), str(port)], cwd=path)
    pid_file.write_text(str(proc.pid))
    print(f"Runtime started: yakoon:{port} (pid {proc.pid})")


def _stop(path: Path) -> None:
    pid_file = path / ".yak" / "runtime.pid"
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"Runtime stopped (pid {pid})")
        except ProcessLookupError:
            print("Runtime not running")
        except ValueError:
            print("Invalid PID file")
        pid_file.unlink(missing_ok=True)
    else:
        print("Runtime not running")


def _status(path: Path) -> None:
    pid_file = path / ".yak" / "runtime.pid"
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            print(f"Runtime running (pid {pid})")
        except (ProcessLookupError, ValueError):
            print("Runtime not running")
    else:
        print("Runtime not running")
