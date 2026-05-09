from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import Command, Request
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.flow import out
from yakoon.base.naming import Key, Namespace
from yakoon.base.runtime.errors import DomainError
from yakoon.ident.models import Group, Membership, User


class CmdMembership(Command):

    key = "membership"
    actions = ["add", "remove", "groups", "users"]

    def __init__(
        self,
        on_project: OnProjectCmd,
        on_list_memberships: OnListMemberships,
        on_list_user_memberships: OnListUserMemberships,
        on_list_group_memberships: OnListGroupMemberships,
        on_add_membership: OnAddMembership,
        on_remove_membership: OnRemoveMembership,
        on_get_namespace: OnGetNamespace,
        on_get_user_by_name: OnGetUserByName,
        on_get_group_by_name: OnGetGroupByName,
    ):
        self.on_project = on_project

        self.on_list_memberships = on_list_memberships
        self.on_list_user_memberships = on_list_user_memberships
        self.on_list_group_memberships = on_list_group_memberships

        self.on_add_membership = on_add_membership
        self.on_remove_membership = on_remove_membership

        self.on_get_namespace = on_get_namespace
        self.on_get_user_by_name = on_get_user_by_name
        self.on_get_group_by_name = on_get_group_by_name

    async def run(self, request: Request):

        action = request.arg(0)

        if action == "add":
            yield await self._add(request)
            return

        if action == "remove":
            yield await self._remove(request)
            return

        if action == "groups":
            yield await self._groups(request)
            return

        if action == "users":
            yield await self._users(request)
            return

        projection = await self.on_project(
            name="membership.error.sam",
            state={
                "reason": (f"Unknown membership action: {action}"),
            },
        )

        yield out(projection)

    async def _add(self, request: Request):

        username = request.arg(1)
        groupname = request.arg(2)

        namespace = self.on_get_namespace()

        user = await self.on_get_user_by_name(name=username)
        if not user:
            raise DomainError(f"User '{username}' not exists.")

        group = await self.on_get_group_by_name(name=groupname)
        if not group:
            raise DomainError(f"Group '{groupname}' not exists.")

        membership = await self.on_add_membership(
            namespace=namespace,
            user_key=user.key,
            group_key=group.key,
        )

        projection = await self.on_project(
            name="membership.add.sam",
            state={
                "membership": membership,
            },
        )

        return out(projection)

    async def _remove(self, request: Request):

        username = request.arg(1)
        groupname = request.arg(2)

        namespace = self.on_get_namespace()

        user = await self.on_get_user_by_name(name=username)
        if not user:
            raise DomainError(f"User '{username}' not exists.")

        group = await self.on_get_group_by_name(name=groupname)
        if not group:
            raise DomainError(f"Group '{groupname}' does not exist.")

        membership = await self.on_remove_membership(
            namespace=namespace,
            user_key=user.key,
            group_key=group.key,
        )

        projection = await self.on_project(
            name="membership.remove.sam",
            state={
                "membership": membership,
            },
        )

        return out(projection)

    async def _groups(self, request: Request):

        username = request.arg(1)

        namespace = self.on_get_namespace()

        user = await self.on_get_user_by_name(name=username)
        if not user:
            raise DomainError(f"User '{username}' does not exist.")

        memberships = await self.on_list_user_memberships(
            namespace=namespace,
            user_key=user.key,
        )

        projection = await self.on_project(
            name="membership.groups.sam",
            state={
                "memberships": memberships,
                "user": username,
            },
        )

        return out(projection)

    async def _users(self, request: Request):

        groupname = request.arg(1)

        namespace = self.on_get_namespace()

        group = await self.on_get_group_by_name(name=groupname)
        if not group:
            raise DomainError(f"Group '{groupname}' not exists.")

        memberships = await self.on_list_group_memberships(
            namespace=namespace,
            group_key=group.key,
        )

        projection = await self.on_project(
            name="membership.users.sam",
            state={
                "memberships": memberships,
                "group": groupname,
            },
        )

        return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnGetUserByName(Protocol):
    async def __call__(self, *, name: str) -> User | None: ...


class OnGetGroupByName(Protocol):
    async def __call__(self, *, name: str) -> Group | None: ...


class OnListMemberships(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
    ) -> list[Membership]: ...


class OnListUserMemberships(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
    ) -> list[Membership]: ...


class OnListGroupMemberships(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        group_key: Key,
    ) -> list[Membership]: ...


class OnAddMembership(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
        group_key: Key,
    ) -> Membership: ...


class OnRemoveMembership(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
        group_key: Key,
    ) -> Membership: ...
