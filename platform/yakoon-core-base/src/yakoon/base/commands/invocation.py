from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Invocation:

    action: str | None = None
    args: list[str] = field(default_factory=list)
    options: list[str] = field(default_factory=list)
    default: bool | None = None

    def usage_data(
        self,
        command: str,
    ) -> dict:

        return {
            "command": command,
            "action": self.action,
            "args": self.args,
            "options": self.options,
        }
