from .ports import GREET
from y5n.api.nodes import NodeSpace


async def run(space: NodeSpace):
    def greet(first_name: str, last_name: str) -> str:
        return f"Hello {first_name} {last_name} from root context!"

    space.ports.provide(GREET, greet)
