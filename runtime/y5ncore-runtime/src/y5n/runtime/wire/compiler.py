from y5n.base.document import Document
from y5n.runtime.document.compiler import (
    Compiler,
    ElementNode,
    build_ast,
    create_mapper,
    normalize_ast,
    tokenize_text,
)


def build_compiler() -> Compiler:

    # --- MAPPING ---

    def mapper(context: dict, root: ElementNode) -> Document:
        mapper = create_mapper(context)
        document = mapper.map_document(root)
        return document

    # --- COMPILING ---

    return Compiler(
        on_tokenize=tokenize_text,
        on_build_ast=build_ast,
        on_normalize_ast=normalize_ast,
        on_build_projection=mapper,
    )
