from yakoon.base.projection import Projection

from .ast import build_ast
from .compiler import Compiler
from .context import ResolverContext
from .mapper import create_mapper
from .nodes import ElementNode
from .normalize import normalize_ast
from .tokens import tokenize_text


def build_compiler() -> Compiler:

    # --- MAPPING ---

    def mapper(ctx: ResolverContext, root: ElementNode) -> Projection:
        mapper = create_mapper(ctx)
        projection = mapper.map_projection(root)
        return projection

    # --- COMPILING ---

    return Compiler(
        on_tokenize=tokenize_text,
        on_build_ast=build_ast,
        on_normalize_ast=normalize_ast,
        on_build_projection=mapper,
    )
