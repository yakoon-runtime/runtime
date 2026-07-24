from __future__ import annotations

from pathlib import Path

from yak.hosts.cli.cwd import find_installation_path


def run(args, mgr) -> None:
    path = args.path or find_installation_path()
    if path is None:
        print("No installation specified. Use --path <dir> or cd into one.")
        return

    import os, signal

    pid_file = Path(path).resolve() / ".yak" / "runtime.pid"
    if pid_file.exists():
        pid = int(pid_file.read_text().strip())
        try:
            os.kill(pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        pid_file.unlink(missing_ok=True)
        print(f"Stopped: {path}")
    else:
        print("No running runtime found.")
