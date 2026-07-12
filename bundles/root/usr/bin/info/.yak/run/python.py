import platform
import time
from datetime import UTC, datetime

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.base.plugins.ports import OnProject

_start_time = time.time()


async def run(space: NodeSpace):
    projection = await space.ports.get(OnProject)(
        space=space,
        state={
            "time": datetime.now(UTC).isoformat(),
            "uptime": _get_uptime(),
            "version": _get_platform_version(),
            "python": platform.python_version(),
            "hostname": platform.node(),
        },
    )
    yield out(projection)


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
