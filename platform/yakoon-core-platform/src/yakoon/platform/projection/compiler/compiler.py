from yakoon.base.projection import Projection

from .ast import build_ast
from .mapper import create_mapper
from .tokens import tokenize_text


class TemplateProjectionCompiler:

    def compile(self, text: str) -> Projection:

        tokens = tokenize_text(text)
        ast = build_ast(tokens)

        mapper = create_mapper()
        projection = mapper.map_projection(ast)

        return projection
