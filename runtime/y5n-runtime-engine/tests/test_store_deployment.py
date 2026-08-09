"""Phase 3 (ADR-18): the runtime collects the store names from the packs.

The runtime knows the logical store names the installed packs declare
(``store: crm`` → the name ``crm``) — nothing more. What each name means
(backend, instance) is deployment knowledge, assembled later by ``yak``.
The tree only *describes* the components; a collector evaluates them.
"""

from __future__ import annotations

from pathlib import Path

from y5n.runtime.engine.executor import ExecutorKind, ExecutorRegistry, RuntimeExecutor
from y5n.runtime.engine.nodes.tree import Tree
from y5n.runtime.engine.services.store_collector import StoreCollector


def _build_tree(root: Path) -> Tree:
    registry = ExecutorRegistry()
    registry.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=root, executors=registry)
    tree.build()
    return tree


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_collector_gets_declared_store_names(tmp_path: Path):
    _write(
        tmp_path / "crm" / "contact" / "add" / ".yak" / "yak.yml",
        "store: crm\n",
    )
    _write(
        tmp_path / "ident" / "grant" / ".yak" / "yak.yml",
        "store: security\n",
    )
    _write(
        tmp_path / "luma" / "box" / ".yak" / "yak.yml",
        "store: luma\n",
    )
    _write(
        tmp_path / "usr" / "bin" / "pwd" / ".yak" / "yak.yml",
        "host: /boot/python/runtime\n",
    )

    tree = _build_tree(tmp_path)

    assert StoreCollector(tree).collect() == ["crm", "luma", "security"]


def test_collector_names_without_duplicates(tmp_path: Path):
    _write(
        tmp_path / "crm" / "contact" / "add" / ".yak" / "yak.yml",
        "store: crm\n",
    )
    _write(
        tmp_path / "crm" / "contact" / "edit" / ".yak" / "yak.yml",
        "store: crm\n",
    )

    tree = _build_tree(tmp_path)

    assert StoreCollector(tree).collect() == ["crm"]


def test_collector_without_stores_is_empty(tmp_path: Path):
    _write(
        tmp_path / "usr" / "bin" / "pwd" / ".yak" / "yak.yml",
        "host: /boot/python/runtime\n",
    )

    tree = _build_tree(tmp_path)

    assert StoreCollector(tree).collect() == []
