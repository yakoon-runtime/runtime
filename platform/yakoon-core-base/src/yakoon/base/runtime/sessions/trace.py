import time
from dataclasses import dataclass, field

from .types import ExecStep


@dataclass(slots=True)
class TraceEntry:
    step: ExecStep
    command: str | None = None
    controller: str | None = None
    request: dict | None = None
    result: dict | None = None
    ts: float = field(default_factory=time.perf_counter)


@dataclass
class ExecutionTrace:

    __slots__ = ("entries",)

    def __init__(self):
        self.entries: list[TraceEntry] = []

    def reset(self):
        self.entries.clear()

    def step(self, step, command=None, controller=None, request=None):
        entry = TraceEntry(
            step=step,
            command=command,
            controller=controller,
            request=request,
        )
        self.entries.append(entry)

    def timeline(self):
        if not self.entries:
            return []

        start = self.entries[0].ts
        prev = start

        result = []

        for e in self.entries:
            runtime = e.ts - start
            delta = e.ts - prev
            prev = e.ts

            result.append((runtime, delta, e))

        return result

    def total_runtime(self):
        if len(self.entries) < 2:
            return 0
        return self.entries[-1].ts - self.entries[0].ts

    def resolved_entry(self):
        for e in self.entries:
            if e.step == ExecStep.COMMAND_RESOLVED:
                return e
        return None

    def first(self, step):
        for e in self.entries:
            if e.step == step:
                return e
        return None
