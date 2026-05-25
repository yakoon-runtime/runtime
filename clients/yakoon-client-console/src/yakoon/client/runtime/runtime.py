from yakoon.platform.machine import RuntimeHost
from yakoon.platform.settings import Settings
from yakoon.platform.wire.runtime import build_runtime


async def create_runtime() -> RuntimeHost:

    settings = Settings()

    runtime = build_runtime(
        settings=settings,
        plugins=[
            "yakoon_spaces.shell",
            "yakoon_spaces.ident",
            # "yakoon.playground",
        ],
        capabilities={},
    )

    return runtime
