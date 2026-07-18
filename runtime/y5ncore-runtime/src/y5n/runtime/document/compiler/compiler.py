from __future__ import annotations

from typing import Protocol

from y5n.base.document import Document

from .ast import ElementNode
from .tokens import Token


class Compiler:

    def __init__(
        self,
        on_tokenize: OnTokenize,
        on_build_ast: OnBuildAst,
        on_normalize_ast: OnNormalizeAst,
        on_build_projection: OnBuildProjection,
    ):

        self.on_tokenize = on_tokenize
        self.on_build_ast = on_build_ast
        self.on_normalize_ast = on_normalize_ast
        self.on_build_projection = on_build_projection

    def compile(self, text: str, context: dict) -> Document:

        tokens = self.on_tokenize(text=text)
        ast = self.on_build_ast(tokens=tokens)

        self.on_normalize_ast(ast)
        return self.on_build_projection(context=context, root=ast)


# ----------------------------------
# PORTS
# ----------------------------------


class OnTokenize(Protocol):
    def __call__(self, *, text: str) -> list[Token]: ...


class OnBuildAst(Protocol):
    def __call__(self, tokens: list[Token]) -> ElementNode: ...


class OnNormalizeAst(Protocol):
    def __call__(self, root: ElementNode) -> None: ...


class OnBuildProjection(Protocol):
    def __call__(self, context: dict, root: ElementNode) -> Document: ...
