"""Architecture guards for ADR-12 (host is a node).

These tests scan the engine source tree. They do not test behavior —
they guard the architecture: if a future change reintroduces a special
host path, these tests fail. Two kinds:

* **Invariant guards** — must pass today and forever (e.g. the runtime
  never imports the boot host implementation).
* **ADR-12 target guards** — fail on this experiment branch and turn
  green as the phases complete; each carries an ``xfail`` reason that
  names the phase that satisfies it.
"""

from __future__ import annotations

from pathlib import Path

import pytest

_ENGINE_SRC = Path(__file__).resolve().parents[1] / "src" / "y5n" / "runtime" / "engine"

# Patterns that only a hand-written coroutine stepper produces. The one
# sanctioned execution driver is FlowCursor (flow/cursor.py).
_STEPPING_PATTERNS = (
    "gen.send(",
    ".send(None)",
    "__await__()",
    "asyncio.ensure_future(",
)


def _python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _sources(root: Path) -> list[tuple[Path, str]]:
    return [(p, p.read_text(encoding="utf-8")) for p in _python_files(root)]


def test_runtime_knows_no_host_implementation():
    """The engine never imports the boot host package (y5n.runtime.boot).

    The runtime coordinates; it must not depend on any concrete host
    implementation. Violations return: engine imports ``y5n.runtime.boot``.
    """
    offenders = [
        str(p.relative_to(_ENGINE_SRC))
        for p, src in _sources(_ENGINE_SRC)
        if "y5n.runtime.boot" in src or "runtime.boot" in src
    ]
    assert not offenders, f"engine imports boot host implementation: {offenders}"


def test_exactly_one_execution_path():
    """Only FlowCursor steps flows; no hand-written coroutine stepper.

    A bespoke stepper (``gen.send``/``__await__()``/``ensure_future``)
    anywhere in the engine means a second execution path has been added.
    """
    offenders = [
        (str(p.relative_to(_ENGINE_SRC)), line.strip())
        for p, src in _sources(_ENGINE_SRC)
        for line in src.splitlines()
        if any(pattern in line for pattern in _STEPPING_PATTERNS)
    ]
    assert not offenders, f"hand-written stepper in engine: {offenders}"


@pytest.mark.xfail(
    reason="ADR-12 Phase 4: _make_host_handler removed from the tree",
    strict=False,
)
def test_tree_never_rewrites_run_handlers():
    """The tree never swaps a node's run handler for a host delegation.

    ``_make_host_handler`` reaches into the tree and rewrites ``node.run``
    at build time — the last special host treatment in the engine. After
    ADR-12 a node with ``host:`` resolves its host via a port lookup and
    the tree stores declarations only.
    """
    tree_src = _ENGINE_SRC / "nodes" / "tree.py"
    src = tree_src.read_text(encoding="utf-8")
    assert "_make_host_handler" not in src, (
        "nodes/tree.py still rewrites run handlers via _make_host_handler"
    )
