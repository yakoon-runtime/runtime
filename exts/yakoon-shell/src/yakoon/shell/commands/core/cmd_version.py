import platform
import subprocess
import time
from datetime import UTC, datetime

from yakoon.base.commands import Command, Request
from yakoon.base.flow import present


class CmdVersion(Command):

    key = "version"

    async def run(self, request: Request):

        projector = await self.create_projector()
        projection = await projector.project(
            "show",
            state={
                "version": get_platform_version(),
                "python": platform.python_version(),
                "hostname": platform.node(),
                "uptime": get_uptime(),
                "time": datetime.now(UTC).isoformat(),
            },
        )
        yield present(projection)


_start_time = time.time()


def get_uptime() -> str:
    """
    Returns the time elapsed since the platform was started,
    formatted as 'Xh Ym'.
    """
    seconds = int(time.time() - _start_time)
    minutes = seconds // 60
    hours = minutes // 60
    return f"{hours}h {minutes % 60}m {seconds % 60}s"


def read_version_file(path="version.txt") -> str | None:
    """
    Reads the platform version from a local file (default: 'version.txt').
    Returns the version string or None if the file does not exist.
    fill the version.txt:
        echo "0.8.2" > version.txt
        docker build -t yakoon .
        COPY version.txt /app/version.txt
    """
    try:
        with open(path) as f:
            return f.read().strip()
    except Exception:
        return None


def get_git_tag() -> str | None:
    """
    Attempts to read the latest Git tag using 'git describe --tags'.
    Returns the tag as a string, or None if unavailable.
    """
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


def get_platform_version() -> str:
    """
    Resolves the platform version in the following order:
    1. Git tag (via 'git describe --tags')
    2. version.txt file
    Returns a string such as 'v0.7.2' or 'unknown'.
    """
    return get_git_tag() or read_version_file() or "unknown"
