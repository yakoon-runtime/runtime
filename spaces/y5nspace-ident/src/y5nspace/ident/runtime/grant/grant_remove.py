from __future__ import annotations

from typing import Protocol

from y5n.base.flow import out
from y5n.base.naming import Namespace
from y5n.base.naming.key import Key
from y5n.base.nodes import NodeSpace, Request

from ...models import PermissionGrant
from ...ports import OnProject
from ...services import Namespaces, PermissionGrantService
from .ports import OnResolveSubject

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    namespaces = space.ports.get(Namespaces)
    permgrant_service = space.ports.get(PermissionGrantService)
    resolve_subject = space.ports.get(OnResolveSubject)

    yield await _handler(
        request=space.request,
        on_project=space.ports.get(OnProject),
        on_get_namespace=namespaces.permgrant_namespace,
        on_remove_grant=permgrant_service.remove_grant,
        on_resolve_subject=resolve_subject,
    )


# ----------------------------------
# HANDLER
# ----------------------------------


async def _handler(
    *,
    request: Request,
    on_project: OnProject,
    on_get_namespace: OnGetNamespace,
    on_remove_grant: OnRemoveGrant,
    on_resolve_subject: OnResolveSubject,
):
    subject_type = request.arg(0)
    subject_name = request.arg(1)
    permission_key = request.arg(2)

    namespace = on_get_namespace()

    subject = await on_resolve_subject(
        subject_type=subject_type,
        subject_name=subject_name,
    )

    grant = await on_remove_grant(
        namespace=namespace,
        subject_key=subject.key,
        permission_key=permission_key,
    )

    projection = await on_project(
        name="grant/remove",
        lang=request.lang,
        state={
            "grant": grant,
        },
    )
    return out(projection)


# ----------------------------------
# PORTS
# ----------------------------------


class OnGetNamespace(Protocol):
    def __call__(self) -> Namespace: ...


class OnRemoveGrant(Protocol):
    async def __call__(
        self,
        *,
        namespace: Namespace,
        subject_key: Key,
        permission_key: str,
    ) -> PermissionGrant: ...
