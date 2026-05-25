from __future__ import annotations

from typing import Protocol

from yakoon.base.nodes import NodeSpace
from yakoon.base.runtime.errors import DomainError

from ...models import Group, User
from ...services import GroupService, Namespaces, UserService
from .ports import OnResolveSubject


async def on_setup(space: NodeSpace):

    namespaces = space.ports.get(Namespaces)
    user_service = space.ports.get(UserService)
    group_service = space.ports.get(GroupService)

    async def get_user_by_name(name: str) -> User | None:
        return await user_service.get_by_username(
            namespace=namespaces.user_namespace(),
            username=name,
        )

    async def get_group_by_name(name: str) -> Group | None:
        return await group_service.get_by_name(
            namespace=namespaces.group_namespace(),
            name=name,
        )

    async def resolve_subject(subject_type: str, subject_name: str) -> User | Group:

        return await _resolve_subject(
            on_get_user_by_name=get_user_by_name,
            on_get_group_by_name=get_group_by_name,
            subject_type=subject_type,
            subject_name=subject_name,
        )

    # ----------------------------------
    # PROVIDE
    # ----------------------------------

    space.ports.provide(OnResolveSubject, resolve_subject)


# ----------------------------------
# INTERNAL
# ----------------------------------


async def _resolve_subject(
    *,
    on_get_user_by_name: OnGetUserByName,
    on_get_group_by_name: OnGetGroupByName,
    subject_type: str,
    subject_name: str,
) -> User | Group:

    if subject_type == "user":
        user = await on_get_user_by_name(name=subject_name)
        if not user:
            raise DomainError(f"User '{subject_name}' " f"does not exist.")
        return user

    if subject_type == "group":
        group = await on_get_group_by_name(name=subject_name)
        if not group:
            raise DomainError(f"Group '{subject_name}' " f"does not exist.")
        return group

    raise DomainError(f"Unknown subject type: " f"{subject_type}")


# ----------------------------------
# PROTOCOLS
# ----------------------------------


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
