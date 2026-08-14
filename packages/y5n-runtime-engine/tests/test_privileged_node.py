"""Tree parsing: `privileged: true` lands on the Node as an invocation flag.

Privileged is an invocation flag (like anonymous): the runtime reads it
from yak.yml, the resolver enforces it, the node itself knows nothing
beyond the flag.
"""

from __future__ import annotations

from pathlib import Path

from y5n.runtime.engine.executor import ExecutorKind, ExecutorRegistry, RuntimeExecutor
from y5n.runtime.engine.nodes.tree import Tree


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)


def _build_tree(root: Path) -> Tree:
    registry = ExecutorRegistry()
    registry.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    tree = Tree(root_path=root, executors=registry)
    tree.build()
    return tree


def test_privileged_defaults_to_false(tmp_path):
    _write(
        tmp_path / "usr" / "bin" / "safe" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Safe",
                "host: /boot/python/runtime",
                "entry:",
                "  run: pack:example.safe:main",
            ]
        ),
    )

    tree = _build_tree(tmp_path)

    node = _find(tree, "usr", "bin", "safe")
    assert node is not None
    assert node.privileged is False


def test_privileged_read_from_yak_yml(tmp_path):
    _write(
        tmp_path / "usr" / "sbin" / "danger" / ".yak" / "yak.yml",
        "\n".join(
            [
                "title: Danger",
                "host: /boot/python/runtime",
                "privileged: true",
                "entry:",
                "  run: pack:example.danger:main",
            ]
        ),
    )

    tree = _build_tree(tmp_path)

    node = _find(tree, "usr", "sbin", "danger")
    assert node is not None
    assert node.privileged is True


def _find(tree: Tree, *parts: str):
    root = tree.root()
    walk = root
    for part in parts:
        walk = walk.get(part)
        if walk is None:
            return None
    return walk
