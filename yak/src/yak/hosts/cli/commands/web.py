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
        case "open":
            _open(path)


def _resolve_path(args) -> Path | None:
    path = Path(args.path).resolve() if args.path else find_installation_path()
    if path is None:
        print("No installation specified. Use --path <dir> or cd into one.")
    return path


def _start(path: Path) -> None:
    python = path / ".venv" / "bin" / "python"
    pid_file = path / ".yak" / "web.pid"

    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            print(f"Web server already running (pid {pid})")
            return
        except (ProcessLookupError, ValueError):
            pid_file.unlink(missing_ok=True)

    proc = subprocess.Popen(
        [str(python), "-m", "y5napp.web"],
        cwd=path,
    )
    pid_file.write_text(str(proc.pid))
    print(f"Web server started (pid {proc.pid})")


def _stop(path: Path) -> None:
    pid_file = path / ".yak" / "web.pid"
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, signal.SIGTERM)
            print(f"Web server stopped (pid {pid})")
        except ProcessLookupError:
            print("Web server not running")
        pid_file.unlink(missing_ok=True)
    else:
        print("Web server not running")


def _status(path: Path) -> None:
    pid_file = path / ".yak" / "web.pid"
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            os.kill(pid, 0)
            print(f"Web server running (pid {pid})")
        except (ProcessLookupError, ValueError):
            print("Web server not running")
    else:
        print("Web server not running")


def _open(path: Path) -> None:
    port = 9100
    config = path / "yakoon-runtime.yml"
    if config.exists():
        try:
            import yaml

            cfg = yaml.safe_load(config.read_text()) or {}
            port = cfg.get("listen", {}).get("port", 9100)
        except Exception:
            pass
    import webbrowser

    url = f"http://localhost:{port}"
    print(f"Opening {url}")
    webbrowser.open(url)
