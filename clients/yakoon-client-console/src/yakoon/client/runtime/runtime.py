from yakoon.base.runtime import Container
from yakoon.compose.runtime import compose_runtime, initialize_storage
from yakoon.platform.machine import RuntimeHost


async def create_runtime() -> RuntimeHost:

    container = Container()

    runtime = compose_runtime(
        container,
        plugins=[
            "yakoon.shell",
            # "yakoon.crm",
            # "yakoon.office",
            # "yakoon.playground",
        ],
        capabilities={
            "audit": "default",
            "discovery": "default",
            "identity": "default",
            "interaction": "default",
            # "jobs": "default",
            "workflow": "default",
        },
    )

    await initialize_storage(container)
    # await seed_demo_system_data(container)

    return runtime
