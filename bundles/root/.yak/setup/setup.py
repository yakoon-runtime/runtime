from y5n.api.nodes import NodeSpace


async def run(space: NodeSpace):

    space.ports.provide("greet", lambda: "Hello from root context!")
