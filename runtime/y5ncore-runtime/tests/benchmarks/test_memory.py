"""Memory benchmark: size of key runtime objects."""

import sys
from uuid import uuid4

from y5n.base.flow.channel import Scope
from y5n.base.flow.primitives import (
    AwaitEvent,
    Background,
    EmitEvent,
    EmitView,
    Foreground,
    Outcome,
    StartCommand,
    StartTask,
    Stop,
    Suspend,
)
from y5n.base.nodes import Node
from y5n.base.projection import Projection
from y5n.base.runtime import Event
from y5n.runtime.flow import Flow, FlowCursor

# ----------------------------------------------------------------
#  Size helpers
# ----------------------------------------------------------------

_SEEN: set[int] | None = None


def _deep_size(obj, depth=0) -> int:
    """Approximate deep size of an object graph."""
    global _SEEN
    if _SEEN is None:
        _SEEN = set()

    obj_id = id(obj)
    if obj_id in _SEEN:
        return 0
    _SEEN.add(obj_id)

    try:
        size = sys.getsizeof(obj)
    except TypeError:
        return 0

    if isinstance(obj, dict):
        for k, v in obj.items():
            size += _deep_size(k, depth + 1)
            size += _deep_size(v, depth + 1)
    elif isinstance(obj, (list, tuple, set, frozenset)):
        for item in obj:
            size += _deep_size(item, depth + 1)
    elif hasattr(obj, "__dict__"):
        size += _deep_size(obj.__dict__, depth + 1)
    elif hasattr(obj, "__slots__"):
        for slot in obj.__slots__:
            try:
                val = getattr(obj, slot)
                size += _deep_size(val, depth + 1)
            except AttributeError:
                pass

    return size


def measure(label: str, obj) -> int:
    global _SEEN
    _SEEN = set()
    size = _deep_size(obj)
    kb = size / 1024
    print(f"  {label:<50s} {size:>8} B  ({kb:.2f} KB)")
    return size


def measure_scenario(label: str, n: int, per_item: int):
    total = per_item * n
    kb = total / 1024
    mb = total / (1024 * 1024)
    print(f"  {label:<50s} {total:>8} B  ({kb:.2f} KB / {mb:.2f} MB)")


# ----------------------------------------------------------------
#  Measurements
# ----------------------------------------------------------------


def run():
    global _SEEN

    print(f"\n{'='*70}")
    print("  SINGLE INSTANCES")
    print(f"{'='*70}\n")

    # Event
    measure("Event(payload='test')", Event(payload="test"))

    # Outcome variants
    measure("Outcome()", Outcome())
    measure(
        "Outcome(control=AwaitEvent)",
        Outcome(control=AwaitEvent("ch", scope=Scope.SESSION)),
    )
    measure(
        "Outcome(effects=[EmitView(...)])",
        Outcome(effects=[EmitView(Projection.create(blocks=[]))]),
    )

    # Effects
    measure("EmitView(projection)", EmitView(Projection.create(blocks=[])))
    measure("Foreground()", Foreground())
    measure("Background()", Background())
    measure(
        'EmitEvent("ch", event, SESSION)',
        EmitEvent("ch", Event(payload="p"), scope=Scope.SESSION),
    )
    measure(
        'StartCommand("ls", "ch")',
        StartCommand("ls", "ch"),
    )
    measure(
        'StartTask("python3", "ch", args=["-c","print(42)"])',
        StartTask("python3", "ch", args=["-c", "print(42)"]),
    )

    # Controls
    measure("Stop()", Stop())
    measure("Suspend()", Suspend())
    measure("AwaitEvent(ch, FLOW)", AwaitEvent("form"))
    measure("AwaitEvent(ch, SESSION)", AwaitEvent("ch", scope=Scope.SESSION))
    measure("AwaitEvent(USER_INPUT)", AwaitEvent("__user__", scope=Scope.USER_INPUT))

    # Flow (idle / waiting)
    node = Node(key="test")
    event = Event(payload="test")
    cursor = FlowCursor("run")

    flow = Flow(
        id="test-flow-123",
        node=node,
        event=event,
        cursor=cursor,
    )
    measure("Flow (idle, no control)", flow)

    flow_wait = Flow(
        id="test-flow-wait",
        node=node,
        event=event,
        cursor=cursor,
        control=AwaitEvent("__user__", scope=Scope.USER_INPUT),
    )
    measure("Flow (waiting USER_INPUT)", flow_wait)

    flow_wait_session = Flow(
        id="test-flow-wait-session",
        node=node,
        event=event,
        cursor=cursor,
        control=AwaitEvent("ch", scope=Scope.SESSION),
    )
    measure("Flow (waiting SESSION)", flow_wait_session)

    # ----------------------------------------------------------------
    print(f"\n{'='*70}")
    print("  MARGINAL (shared Node/Event/Cursor)")
    print(f"{'='*70}\n")

    # When 100k flows share the same Node + Event + Cursor,
    # only the Flow instance + Control is per-flow marginal cost.
    # Measure the Flow object itself (no walk into shared refs)
    _SEEN = set()

    flow_bare = Flow(id=str(uuid4()), node=node, event=event, cursor=cursor)
    flow_bare_size = sys.getsizeof(flow_bare)
    await_size = sys.getsizeof(AwaitEvent("ch", scope=Scope.SESSION))
    marginal = flow_bare_size + await_size
    print(
        f"  sys.getsizeof(Flow instance)           {flow_bare_size:>8} B  ({flow_bare_size/1024:.2f} KB)"
    )
    print(
        f"  sys.getsizeof(AwaitEvent)              {await_size:>8} B  ({await_size/1024:.2f} KB)"
    )
    print("  ─────────────────────────────────────────────")
    print(
        f"  Marginal cost per waiting flow         {marginal:>8} B  ({marginal/1024:.2f} KB)"
    )

    for n in [10_000, 50_000, 100_000, 1_000_000]:
        total = marginal * n
        print(
            f"  Marginal × {n:<7,}                    {total:>8} B  ({total/1024:.2f} KB / {total/(1024*1024):.2f} MB)"
        )

    print()
    print(f"\n{'='*70}")
    print("  SCENARIOS (estimate)")
    print(f"{'='*70}\n")

    for n in [10_000, 50_000, 100_000]:
        print(f"  --- {n:,} flows ---")

        _SEEN = set()
        per_flow = _deep_size(flow_wait)
        measure_scenario(f"Flow (wait USER_INPUT) × {n}", n, per_flow)

        _SEEN = set()
        per_flow_s = _deep_size(flow_wait_session)
        measure_scenario(f"Flow (wait SESSION)   × {n}", n, per_flow_s)

        print()

    print(f"\n{'='*70}")
    print("  NOTES")
    print(f"{'='*70}\n")
    print("  - Sizes include full object graph (nested objects)")
    print("  - Overlap (shared Node, Event, etc.) NOT subtracted")
    print("  - Real multi-flow memory is lower (shared Node objects)")
    print()


if __name__ == "__main__":
    run()
