import platform
import time
from datetime import UTC, datetime

from y5n.sdk import ports

_start_time = time.time()


async def main():
    projection = ports.get("projection")

    text = projection.render(
        name="default",
        state={
            "time": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S UTC"),
            "uptime": _get_uptime(),
            "version": _get_platform_version(),
            "python": platform.python_version(),
            "hostname": platform.node(),
        },
    )
    print(text)


def _get_uptime() -> str:
    seconds = int(time.time() - _start_time)
    minutes = seconds // 60
    hours = minutes // 60
    return f"{hours}h {minutes % 60}m {seconds % 60}s"


def _get_platform_version() -> str:
    return _get_git_tag() or "unknown"


def _get_git_tag() -> str | None:
    import subprocess

    try:
        return (
            subprocess.check_output(
                ["git", "describe", "--tags"], stderr=subprocess.DEVNULL
            )
            .decode()
            .strip()
        )
    except Exception:
        return None
