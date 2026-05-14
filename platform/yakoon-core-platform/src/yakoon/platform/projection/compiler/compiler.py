from __future__ import annotations

from typing import Protocol

from yakoon.base.projection import Projection

from .ast import ElementNode
from .context import ResolverContext
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

    def compile(self, text: str, ctx: ResolverContext) -> Projection:

        tokens = self.on_tokenize(text=text)
        ast = self.on_build_ast(tokens=tokens)

        self.on_normalize_ast(ast)
        return self.on_build_projection(ctx=ctx, root=ast)


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
    def __call__(self, ctx: ResolverContext, root: ElementNode) -> Projection: ...
