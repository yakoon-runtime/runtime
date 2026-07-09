# services/permissions/resolver.py

from __future__ import annotations

from typing import Protocol

from y5n.api.naming import Key, Namespace
from y5n.api.permissions import PermissionSet
from y5n.api.ports import OnNewPermissionSet, OnParsePermissionSpec

from ...models.ident import Join, PermissionGrant


class PermissionResolver:
    """IAM-Architecture"""

    def __init__(
        self,
        on_new_permissionset: OnNewPermissionSet,
        on_list_user_joins: OnListUserJoins,
        on_list_subject_grants: OnListSubjectGrants,
        on_parse_spec: OnParsePermissionSpec,
    ):
        self.on_new_permissionset = on_new_permissionset
        self.on_list_user_joins = on_list_user_joins
        self.on_list_subject_grants = on_list_subject_grants
        self.on_parse_spec = on_parse_spec

    # ----------------------------------
    # RESOLVE
    # ----------------------------------

    async def resolve_user_permissions(
        self,
        *,
        grant_namespace: Namespace,
        join_namespace: Namespace,
        user_key: Key,
    ) -> PermissionSet:

        out = self.on_new_permissionset()

        direct_grants = await self.on_list_subject_grants(
            namespace=grant_namespace,
            subject_key=user_key,
        )

        self._merge_grants(out, direct_grants)

        joins = await self.on_list_user_joins(
            namespace=join_namespace,
            user_key=user_key,
        )

        for join in joins:
            grants = await self.on_list_subject_grants(
                namespace=grant_namespace,
                subject_key=(join.group_key),
            )

            self._merge_grants(out, grants)

        return out

    # ----------------------------------
    # INTERNAL
    # ----------------------------------

    def _merge_grants(
        self,
        target: PermissionSet,
        grants: list[PermissionGrant],
    ):
        for grant in grants:
            spec = f"{grant.permission_key}" f"|{grant.bits}"
            if grant.deny:
                spec = f"-{spec}"

            permission = self.on_parse_spec(spec=spec)
            target.add(permission)


# ----------------------------------
# PORTS
# ----------------------------------


class OnListUserJoins(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        user_key: Key,
    ) -> list[Join]: ...


class OnListSubjectGrants(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
    ) -> list[PermissionGrant]: ...
