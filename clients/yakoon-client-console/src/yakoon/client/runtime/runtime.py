from yakoon.compose.runtime import compose_runtime
from yakoon.platform.machine import RuntimeHost
from yakoon.platform.settings import Settings


async def create_runtime() -> RuntimeHost:

    settings = Settings()

    runtime = compose_runtime(
        settings=settings,
        plugins=[
            "yakoon.shell",
            "yakoon.ident",
            # "yakoon.crm",
            # "yakoon.office",
            # "yakoon.playground",
        ],
        capabilities={},
    )

    return runtime
