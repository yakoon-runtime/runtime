from yakoon.base.projection import Projection

from .ast import build_ast
from .mapper import Mapper
from .tokens import tokenize_text


class TemplateProjectionCompiler:

    def compile(self, text: str) -> Projection:

        tokens = tokenize_text(text)
        ast = build_ast(tokens)

        mapper = Mapper()
        projection = mapper.map_projection(ast)

        return projection
