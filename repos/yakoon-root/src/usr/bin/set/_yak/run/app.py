from y5n.api.dsl import out_text
from y5n.api.nodes import NodeSpace
from y5n.base.runtime.input import Interaction

SETTINGS = ("interaction",)


async def run(space: NodeSpace):
    for opt in SETTINGS:
        if space.request.has_option(opt):
            value = space.request.option(opt)
            yield _apply(space, opt, value)


def _apply(space, key: str, value: str):
    if key == "interaction":
        try:
            space.session.interaction = Interaction(value)
        except ValueError:
            valid = ", ".join(m.value for m in Interaction)
            return out_text(f"Invalid interaction mode. Valid: {valid}")
        return out_text(f"interaction set to {value}")
    return out_text(f"Unknown setting: {key}")
