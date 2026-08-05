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


def test_dispatch_handler_has_no_host_knowledge():
    """The dispatch handler routes to a declared node — no host specifics.

    A node declares ``host:`` in yak.yml; ``_make_dispatch_handler`` finds
    that node in the tree and runs it. The handler must stay a pure
    dispatcher: it may only look up the declared node by path and call its
    ``run()``. It must never learn what a host is (no import of the boot
    implementation, no host-type branching, no scheme interpretation).
    """
    tree_src = _ENGINE_SRC / "nodes" / "tree.py"
    src = tree_src.read_text(encoding="utf-8")

    assert "y5n.runtime.boot" not in src, (
        "dispatch handler would reach into a concrete host implementation"
    )
    assert "_make_dispatch_handler" in src, (
        "nodes/tree.py lost its dispatch handler — host routing broken"
    )
