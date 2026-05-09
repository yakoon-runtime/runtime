from __future__ import annotations

from typing import Protocol

from yakoon.base.commands import Command, Request
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.flow import out
from yakoon.base.naming import Key, Namespace
from yakoon.base.runtime.errors import DomainError
from yakoon.ident.models import (
    Group,
    PermissionGrant,
    User,
)


class CmdPermissionGrant(Command):

    key = "grant"
    subcommands = ["add", "remove", "user", "group", "permission"]

    def __init__(
        self,
        on_project: OnProjectCmd,
        on_list_grants: OnListGrants,
        on_list_subject_grants: OnListSubjectGrants,
        on_list_permission_grants: OnListPermissionGrants,
        on_add_grant: OnAddGrant,
        on_remove_grant: OnRemoveGrant,
        on_get_namespace: OnGetNamespace,
        on_get_user_by_name: OnGetUserByName,
        on_get_group_by_name: OnGetGroupByName,
    ):
        self.on_project = on_project
        self.on_list_grants = on_list_grants
        self.on_list_subject_grants = on_list_subject_grants
        self.on_list_permission_grants = on_list_permission_grants
        self.on_add_grant = on_add_grant
        self.on_remove_grant = on_remove_grant
        self.on_get_namespace = on_get_namespace
        self.on_get_user_by_name = on_get_user_by_name
        self.on_get_group_by_name = on_get_group_by_name

    async def run(
        self,
        request: Request,
    ):
        action = request.arg(0)

        if action == "add":
            yield await self._add(request)
            return

        if action == "remove":
            yield await self._remove(request)
            return

        if action == "user":
            yield await self._user(request)
            return

        if action == "group":
            yield await self._group(request)
            return

        if action == "permission":
            yield await self._permission(request)
            return

        projection = await self.on_project(
            name="grant.error.sam",
            state={
                "reason": (f"Unknown permission action: " f"{action}"),
            },
        )

        yield out(projection)

    async def _add(
        self,
        request: Request,
    ):
        subject_type = request.arg(1)
        subject_name = request.arg(2)

        permission_key = request.arg(3)

        bits = request.option("bits") or "x"

        deny = bool(request.option("deny"))

        namespace = self.on_get_namespace()

        subject = await self._resolve_subject(
            subject_type=subject_type,
            subject_name=subject_name,
        )

        grant = await self.on_add_grant(
            namespace=namespace,
            subject_key=subject.key,
            permission_key=permission_key,
            bits=bits,
            deny=deny,
        )

        projection = await self.on_project(
            name="grant.add.sam",
            state={
                "grant": grant,
            },
        )

        return out(projection)

    async def _remove(
        self,
        request: Request,
    ):
        subject_type = request.arg(1)
        subject_name = request.arg(2)

        permission_key = request.arg(3)

        namespace = self.on_get_namespace()

        subject = await self._resolve_subject(
            subject_type=subject_type,
            subject_name=subject_name,
        )

        grant = await self.on_remove_grant(
            namespace=namespace,
            subject_key=subject.key,
            permission_key=permission_key,
        )

        projection = await self.on_project(
            name="grant.remove.sam",
            state={
                "grant": grant,
            },
        )

        return out(projection)

    async def _user(
        self,
        request: Request,
    ):
        username = request.arg(1)
        namespace = self.on_get_namespace()

        user = await self.on_get_user_by_name(name=username)
        if not user:
            raise DomainError(f"User '{username}' " f"does not exist.")

        grants = await self.on_list_subject_grants(
            namespace=namespace,
            subject_key=user.key,
        )

        projection = await self.on_project(
            name="grant.user.sam",
            state={
                "user": username,
                "grants": grants,
            },
        )

        return out(projection)

    async def _group(
        self,
        request: Request,
    ):

        groupname = request.arg(1)

        namespace = self.on_get_namespace()

        group = await self.on_get_group_by_name(
            name=groupname,
        )

        if not group:
            raise DomainError(f"Group '{groupname}' " f"does not exist.")

        grants = await self.on_list_subject_grants(
            namespace=namespace,
            subject_key=group.key,
        )

        projection = await self.on_project(
            name="grant.group.sam",
            state={
                "group": groupname,
                "grants": grants,
            },
        )

        return out(projection)

    async def _permission(
        self,
        request: Request,
    ):

        permission_key = request.arg(1)

        namespace = self.on_get_namespace()

        grants = await self.on_list_permission_grants(
            namespace=namespace,
            permission_key=permission_key,
        )

        projection = await self.on_project(
            name="grant.permission.sam",
            state={
                "permission": permission_key,
                "grants": grants,
            },
        )

        return out(projection)

    # ----------------------------------
    # INTERNAL
    # ----------------------------------

    async def _resolve_subject(
        self,
        *,
        subject_type: str,
        subject_name: str,
    ) -> User | Group:

        if subject_type == "user":
            user = await self.on_get_user_by_name(name=subject_name)
            if not user:
                raise DomainError(f"User '{subject_name}' " f"does not exist.")
            return user

        if subject_type == "group":
            group = await self.on_get_group_by_name(name=subject_name)
            if not group:
                raise DomainError(f"Group '{subject_name}' " f"does not exist.")
            return group

        raise DomainError(f"Unknown subject type: " f"{subject_type}")


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnGetUserByName(Protocol):
    async def __call__(
        self,
        *,
        name: str,
    ) -> User | None: ...


class OnGetGroupByName(Protocol):
    async def __call__(
        self,
        *,
        name: str,
    ) -> Group | None: ...


class OnListGrants(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
    ) -> list[PermissionGrant]: ...


class OnListSubjectGrants(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
    ) -> list[PermissionGrant]: ...


class OnListPermissionGrants(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        permission_key: str,
    ) -> list[PermissionGrant]: ...


class OnAddGrant(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
        permission_key: str,
        bits: str = "x",
        deny: bool = False,
    ) -> PermissionGrant: ...


class OnRemoveGrant(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
        permission_key: str,
    ) -> PermissionGrant: ...
