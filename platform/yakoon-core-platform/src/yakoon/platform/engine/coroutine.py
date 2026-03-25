import inspect

from yakoon.base.runtime.steps import Outcome


def ensure_step(run_fn):

    def factory(command, request):

        result = run_fn(command, request)

        # --- async generator ---
        if inspect.isasyncgen(result):
            return result

        # --- coroutine ---
        if inspect.iscoroutine(result):

            async def coro_wrapper():
                await result
                yield Outcome()

            return coro_wrapper()

        # --- None ---
        if result is None:

            async def empty():
                yield Outcome()

            return empty()

        raise TypeError(...)

    return factory
