from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Invocation:

    action: str | None = None
    args: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    default: bool | None = None

    def usage(
        self,
        command: str,
    ) -> str:
        parts = [command]
        if self.action:
            parts.append(self.action)

        for arg in self.args:
            parts.append(f"<{arg}>")

        for opt in self.options:
            parts.append(f"--{opt} <{opt}>")

        return "usage: " + " ".join(parts)
