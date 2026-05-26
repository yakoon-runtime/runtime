from y5n.base.projection import Projection
from y5n.runtime.projection.compiler import (
    Compiler,
    ElementNode,
    build_ast,
    create_mapper,
    normalize_ast,
    tokenize_text,
)


def build_compiler() -> Compiler:

    # --- MAPPING ---

    def mapper(context: dict, root: ElementNode) -> Projection:
        mapper = create_mapper(context)
        projection = mapper.map_projection(root)
        return projection

    # --- COMPILING ---

    return Compiler(
        on_tokenize=tokenize_text,
        on_build_ast=build_ast,
        on_normalize_ast=normalize_ast,
        on_build_projection=mapper,
    )
