from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import Command, Invocation, Request
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.flow import out
from yakoon.base.naming import Namespace
from yakoon.ident.models import Group


class CmdGroup(Command):

    key = "group"

    invocations = [
        Invocation(action="list", default=True),
        Invocation(action="add", args=["groupname"]),
        Invocation(action="delete", args=["groupname"]),
        Invocation(action="edit", args=["groupname"], options=["enabled"]),
    ]

    def __init__(
        self,
        on_project: OnProjectCmd,
        on_list_groups: OnListGroups,
        on_add_group: OnAddGroup,
        on_edit_group: OnEditGroup,
        on_delete_group: OnDeleteGroup,
        on_get_namspace: OnGetNamespace,
    ):
        self.on_project = on_project
        self.on_list_groups = on_list_groups
        self.on_add_group = on_add_group
        self.on_edit_group = on_edit_group
        self.on_delete_group = on_delete_group
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

    async def _list(self, request: Request):
        namespace = self.on_get_namspace()
        groups = await self.on_list_groups(namespace=namespace)

        projection = await self.on_project(
            name="group.list.sam",
            state={
                "groups": groups,
            },
        )
        return out(projection)

    async def _add(self, request: Request):
        groupname = request.arg(1)

        namespace = self.on_get_namspace()
        group = await self.on_add_group(
            namespace=namespace,
            name=groupname,
        )

        projection = await self.on_project(
            name="group.add.sam",
            state={
                "group": group,
            },
        )
        return out(projection)

    async def _edit(self, request: Request):

        groupname = request.arg(1)

        changes = {
            "enabled": request.option("enabled"),
        }

        namespace = self.on_get_namspace()
        group = await self.on_edit_group(
            namespace=namespace,
            name=groupname,
            changes=changes,
        )

        projection = await self.on_project(
            name="group.edit.sam",
            state={
                "group": group,
            },
        )
        return out(projection)

    async def _delete(self, request: Request):
        groupname = request.arg(1)

        namespace = self.on_get_namspace()
        await self.on_delete_group(
            namespace=namespace,
            name=groupname,
        )

        projection = await self.on_project(
            name="group.delete.sam",
            state={
                "group": groupname,
            },
        )
        return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnListGroups(Protocol):
    async def __call__(self, namespace: Namespace) -> list[Group]: ...


class OnAddGroup(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        name: str,
    ) -> Group: ...


class OnEditGroup(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        name: str,
        changes: dict,
    ) -> Group: ...


class OnDeleteGroup(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        name: str,
    ) -> None: ...
