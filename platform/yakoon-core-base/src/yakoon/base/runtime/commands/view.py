from .steps.step import Ask, Show

# -----------------------------
# COMPILE
# -----------------------------


async def compile_view(view, *, policy_service):

    for block in view.blocks:

        if block.type == "fields":
            yield Ask(block, policy_service)
        else:
            yield Show(block)
