from __future__ import annotations

from pathlib import Path

from y5n.runtime.engine.executor import ExecutorKind, ExecutorRegistry, RuntimeExecutor
from y5n.runtime.engine.nodes.tree import Tree


def _build_tree(root: Path) -> Tree:
    registry = ExecutorRegistry()
    registry.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=root, executors=registry)
    tree.build()
    return tree


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def test_node_reads_declared_store(tmp_path: Path):
    _write(
        tmp_path / "crm" / "contact" / "add" / ".yak" / "yak.yml",
        "\n".join(
            [
                "host: /boot/python/runtime",
                "entry:",
                "  run: pack:x:run",
                "store: crm",
            ]
        ),
    )
    tree = _build_tree(tmp_path)

    node = tree.find("/crm/contact/add")
    assert node is not None
    assert node.store == "crm"


def test_node_without_store_is_none(tmp_path: Path):
    _write(
        tmp_path / "usr" / "bin" / "pwd" / ".yak" / "yak.yml",
        "\n".join(
            [
                "host: /boot/python/runtime",
                "entry:",
                "  run: pack:x:run",
            ]
        ),
    )
    tree = _build_tree(tmp_path)

    node = tree.find("/usr/bin/pwd")
    assert node is not None
    assert node.store is None


def test_non_string_store_is_ignored(tmp_path: Path):
    _write(
        tmp_path / "opt" / "app" / ".yak" / "yak.yml",
        "\n".join(
            [
                "host: /boot/python/runtime",
                "entry:",
                "  run: pack:x:run",
                "store:",
                "  profile: crm",
            ]
        ),
    )
    tree = _build_tree(tmp_path)

    node = tree.find("/opt/app")
    assert node is not None
    assert node.store is None
