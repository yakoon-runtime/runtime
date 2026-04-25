from yakoon.base.projection import Projection

from .ast import build_ast
from .context import ResolverContext
from .mapper import create_mapper
from .tokens import tokenize_text


class TemplateProjectionCompiler:

    def compile(self, text: str, ctx: ResolverContext) -> Projection:

        tokens = tokenize_text(text)
        ast = build_ast(tokens)

        mapper = create_mapper(ctx)
        projection = mapper.map_projection(ast)

        return projection
