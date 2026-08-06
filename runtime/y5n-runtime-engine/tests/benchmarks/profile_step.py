"""Profile the engine step: where do the ops/s go?

Measures the per-step cost of the parts that changed in the ADR-12
migration, with clean timing.

Run: .venv/bin/python runtime/y5n-runtime-engine/tests/benchmarks/profile_step.py
"""

from __future__ import annotations

import asyncio
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
for src in (
    ROOT / "runtime" / "y5n-runtime-api" / "src",
    ROOT / "runtime" / "y5n-runtime-engine" / "src",
    ROOT / "runtime" / "y5n-runtime-store" / "src",
    ROOT / "runtime" / "y5n-runtime-boot" / "src",
    ROOT / "sdk" / "y5n-sdk-python" / "src",
):
    sys.path.insert(0, str(src))

from y5n.runtime.api.naming import Key  # noqa: E402,I001
from y5n.runtime.engine.nodes import Node  # noqa: E402
from y5n.runtime.api.runtime.context import set_context  # noqa: E402
from y5n.runtime.engine.runtime.invocation import derive_invocation_context  # noqa: E402
from y5n.runtime.engine.runtime.sessions.session import Session, SessionData  # noqa: E402

N = 200_000


def bench(label: str, fn) -> None:
    best = float("inf")
    for _ in range(3):
        start = time.perf_counter()
        fn()
        elapsed = time.perf_counter() - start
        best = min(best, elapsed)
    ops = N / best
    print(f"  {label:<40} {ops:>12,.0f} ops/s  ({best*1000:.2f} ms for {N})")


def make_session() -> Session:
    s = Session(key=Key.from_parts("t", "s", "r", "1"), data=SessionData())
    s.set_data("fs:root", "/tmp/ws")
    s.set_cwd("/")
    return s


def bench_derive_invocation_context() -> None:
    s = make_session()
    node = Node(key="cd")

    def run():
        for _ in range(N):
            derive_invocation_context(
                node=node, session=s, flow_id="f1", tokens=["/opt"]
            )

    bench("derive_invocation_context (dict + Session access)", run)


def bench_contextvar_set_raw() -> None:
    data = {"node": {"path": "/cd"}, "args": ["/opt"]}

    def run():
        for _ in range(N):
            set_context(data)

    bench("ContextVar.set(raw dict)", run)


def bench_dict_build_only() -> None:
    """The dict construction alone (what derive_invocation_context builds)."""

    def run():
        for _ in range(N):
            path = "/cd"
            name = "cd"
            _ = {
                "node": {"path": path, "name": name},
                "cwd": "/",
                "workspace": "/tmp/ws",
                "user": {"id": None, "name": None},
                "session": {
                    "key": "t/s/r#1",
                    "lang": "en",
                    "interaction": "cli",
                    "data": {},
                },
                "flow": {"id": "f1", "key": "cd"},
                "args": ["/opt"],
            }

    bench("dict construction only", run)


def bench_cursor_next() -> None:
    """async: one cursor.next per 100-yield handler."""
    from y5n.runtime.engine.flow.cursor import FlowCursor  # noqa: E402

    async def handler():
        for _ in range(100):
            yield 1

    node = Node(key="test", run=handler)
    count = N // 100

    async def run():
        for _ in range(count):
            cursor = FlowCursor("run")
            await cursor.next(node)

    async def main():
        best = float("inf")
        for _ in range(3):
            start = time.perf_counter()
            await run()
            elapsed = time.perf_counter() - start
            best = min(best, elapsed)
        ops = count / best
        print(
            f"  {'FlowCursor.next (100 yields)':<40} {ops:>12,.0f} cursors/s  ({best*1000:.2f} ms for {count})"
        )

    asyncio.run(main())


def main() -> None:
    print(f"Per-step cost profile (N={N}):\n")
    bench_derive_invocation_context()
    bench_dict_build_only()
    bench_contextvar_set_raw()
    bench_cursor_next()


if __name__ == "__main__":
    main()
