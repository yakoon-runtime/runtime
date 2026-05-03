from __future__ import annotations

from typing import Protocol


class PermissionBootstrap:

    def __init__(self, on_register: OnRegisterRole) -> None:
        self.on_register = on_register

    async def apply(self):
        await self.on_register(
            "admin",
            [
                "shell-app:use|rx",
            ],
        )
        await self.on_register(
            "user",
            [
                "shell-app:use|rx",
            ],
        )


# ----------------------------------
# PORTS
# ----------------------------------


class OnRegisterRole(Protocol):
    async def __call__(self, name: str, specs: list[str]) -> None: ...
