from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import Command, Invocation, Request
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.ident.models import User


class CmdUser(Command):

    key = "user"

    invocations = [
        Invocation(action="add", args=["username"], options=["password"]),
        Invocation(action="delete", args=["username"]),
        Invocation(
            action="edit",
            args=["username"],
            options=["password", "enabled"],
        ),
    ]

    def __init__(
        self,
        on_project: OnProjectCmd,
        on_list_users: OnListUsers,
        on_add_user: OnAddUser,
        on_edit_user: OnEditUser,
        on_delete_user: OnDeleteUser,
        on_get_namspace: OnGetNamespace,
    ):
        self.on_project = on_project
        self.on_list_users = on_list_users
        self.on_add_user = on_add_user
        self.on_edit_user = on_edit_user
        self.on_delete_user = on_delete_user
        self.on_get_namspace = on_get_namspace

    async def run(self, request: Request):
        action = request.arg(0)

        if not action or action == "list":
            yield await self._list(request)
            return

        if action == "add":
            yield await self._add(request)
            return

        if action == "edit":
            yield await self._edit(request)
            return

        if action == "delete":
            yield await self._delete(request)
            return

        projection = await self.on_project(
            name="user.error.sam",
            state={
                "reason": f"Unknown user action: {action}",
            },
        )
        yield out(projection)

    async def _list(self, request: Request):
        namespace = self.on_get_namspace()
        users = await self.on_list_users(namespace=namespace)

        projection = await self.on_project(
            name="user.list.sam",
            state={
                "users": users,
            },
        )
        return out(projection)

    async def _add(self, request: Request):
        username = request.arg(1)
        password = request.option("password")

        namespace = self.on_get_namspace()
        user = await self.on_add_user(
            namespace=namespace,
            username=username,
            password=password,
        )

        projection = await self.on_project(
            name="user.add.sam",
            state={
                "user": user,
            },
        )
        return out(projection)

    async def _edit(self, request: Request):

        username = request.arg(1)

        changes = {
            "password": request.option("password"),
            "enabled": request.option("enabled"),
        }

        namespace = self.on_get_namspace()
        user = await self.on_edit_user(
            namespace=namespace,
            username=username,
            changes=changes,
        )

        projection = await self.on_project(
            name="user.edit.sam",
            state={
                "user": user,
            },
        )
        return out(projection)

    async def _delete(self, request: Request):
        username = request.arg(1)

        namespace = self.on_get_namspace()
        await self.on_delete_user(
            namespace=namespace,
            username=username,
        )

        projection = await self.on_project(
            name="user.delete.sam",
            state={
                "user": username,
            },
        )
        return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnListUsers(Protocol):
    async def __call__(self, namespace: Namespace) -> list[User]: ...


class OnAddUser(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        username: str,
        password: str | None,
    ) -> User: ...


class OnEditUser(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        username: str,
        changes: dict,
    ) -> User: ...


class OnDeleteUser(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        username: str,
    ) -> None: ...
