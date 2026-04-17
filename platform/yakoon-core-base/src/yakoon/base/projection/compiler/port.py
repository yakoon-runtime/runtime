from yakoon.base.projection import Projection

from .context import ResolverContext


class ProjectionCompiler:

    def compile(self, text: str, ctx: ResolverContext) -> Projection: ...
