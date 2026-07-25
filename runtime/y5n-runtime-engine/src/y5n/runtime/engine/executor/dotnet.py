"""Dotnet executor — placeholder, not yet implemented."""

from .base import Executor


class DotnetExecutor(Executor):
    async def run(self, node, phase, space):
        raise NotImplementedError(".NET executor is not yet supported")
