from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import Command, Request
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.commands.types import CommandScope
from yakoon.base.flow import out
from yakoon.base.naming import Key
from yakoon.base.plugins.models import AuthResult


class CmdSu(Command):

    key = "su"
    scope = CommandScope.SHELL

    def __init__(
        self,
        on_project: OnProjectCmd,
        on_set_identity: OnSetIdentity,
        on_authenticate: OnAuthenticateUser,
        on_store_session: OnStoreSession,
        on_apply_perm: OnApplyPermissions,
    ):
        self.on_project = on_project
        self.on_set_identity = on_set_identity
        self.on_authenticate = on_authenticate
        self.on_store_session = on_store_session
        self.on_apply_perm = on_apply_perm

    async def run(self, request: Request):

        username = request.arg(0) or request.option("user")
        secret = request.option("password")
        if not secret:
            # secret = await projector.require_first("ask_secret")
            if secret:
                secret = secret.reveal()

        result = await self.on_authenticate(username, secret)
        if result.ok and result.account:

            account = result.account
            self.on_set_identity(account["key"], account["username"])

            self.on_apply_perm(
                roles=account["roles"],
                permissions=account["permissions"],
            )

            await self.on_store_session()

            projection = await self.on_project(
                name="success.sam",
                state={
                    "user": username,
                },
            )
        else:
            projection = await self.on_project(
                name="error.sam",
                state={
                    "user": username,
                    "reason": result.reason,
                },
            )

        yield out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnSetIdentity(Protocol):
    def __call__(self, key: Key, user_name: str): ...


class OnAuthenticateUser(Protocol):
    async def __call__(self, username: str, secret: str) -> AuthResult: ...


class OnStoreSession(Protocol):
    async def __call__(self): ...


class OnApplyPermissions(Protocol):
    def __call__(
        self,
        roles: list[str],
        permissions: list[str],
    ): ...
