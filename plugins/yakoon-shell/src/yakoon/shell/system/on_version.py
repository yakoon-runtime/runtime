import platform
import subprocess
import time
from datetime import UTC, datetime

from yakoon.base.flow import out
from yakoon.base.nodes import RuntimeContext
from yakoon.base.plugins.ports import OnProject

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_version(ctx: RuntimeContext):

    resource = ctx.resource(
        "list",
        scope="version",
        lang=ctx.session.lang,
    )

    projection = await ctx.ports.get(OnProject)(
        resource=resource,
        state={
            "time": datetime.now(UTC).isoformat(),
            "uptime": _get_uptime(),
            "version": _get_platform_version(),
            "python": platform.python_version(),
            "hostname": platform.node(),
        },
    )

    yield out(projection)


_start_time = time.time()

# ----------------------------------
# INTERNALS
# ----------------------------------


def _get_uptime() -> str:
    """
    Returns the time elapsed since the platform was started,
    formatted as 'Xh Ym'.
    """
    seconds = int(time.time() - _start_time)
    minutes = seconds // 60
    hours = minutes // 60
    return f"{hours}h {minutes % 60}m {seconds % 60}s"


def _get_platform_version() -> str:
    """
    Resolves the platform version in the following order:
    1. Git tag (via 'git describe --tags')
    2. version.txt file
    Returns a string such as 'v0.7.2' or 'unknown'.
    """
    return _get_git_tag() or _read_version_file() or "unknown"


def _read_version_file(path="version.txt") -> str | None:
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


def _get_git_tag() -> str | None:
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
