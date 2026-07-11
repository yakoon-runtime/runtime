from y5n.api.dsl import out, view
from y5n.api.nodes import NodeSpace
from y5n.base.plugins.ports import OnCompile, OnJinjaRender


async def run(space: NodeSpace):
    greet = space.ports.get("greet")
    result = greet()

    template = '<heading>Test Bundle</heading>\n<br/>\n{{ greeting }}\n<br count="2"/>\n<rule/>\nrendered via projection'
    html = space.ports.get(OnJinjaRender)(template, context={"greeting": result})
    projection = space.ports.get(OnCompile)(text=html, context={})

    yield view(clear=True)
    yield out(projection)
