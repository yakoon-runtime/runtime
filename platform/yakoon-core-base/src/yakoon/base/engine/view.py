from .step import Ask, Show

# -----------------------------
# CORE
# -----------------------------


async def _run_view(view, *, policy_service, collect=False):

    results = {} if collect else None

    for block in view.blocks:

        if block.type == "fields":
            data = yield Ask(block, policy_service)

            if collect:
                results.update(data)

        else:
            yield Show(block)

    if collect:
        return results


# -----------------------------
# COMPILE
# -----------------------------


def compile_view(view, *, policy_service):
    """
    usage:
        yield from run_view(view, policy_service=policy, collect=False)
    """

    async def flow(command, session, request):
        async for step in _run_view(view, policy_service=policy_service, collect=False):
            yield step

    return flow


# -----------------------------
# COLLECT
# -----------------------------


async def collect_view(view, *, policy_service):
    """
    usage:
       results = yield from run_view(view, policy_service=policy, collect=True)
    """

    result = None

    async for step in _run_view(view, policy_service=policy_service, collect=True):
        result = yield step

    return result
