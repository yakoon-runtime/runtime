from __future__ import annotations

from y5n.api.naming import Key
from y5n.sdk import ports
from y5nstore.event.wire import build_store

from .bootstrap import bootstrap
from .models import User, UserData
from .services import (
    AccountService,
    AllowAllSecretVerifier,
    AuthenticationService,
    GroupService,
    JoinService,
    Namespaces,
    PermissionGrantService,
    UserService,
)
from .settings import Settings


async def main():

    settings = Settings()
    store = build_store(settings.storage)
    await _build_index(store)

    service_ns = Namespaces()

    users = UserService(
        on_get=store.objects.get,
        on_append=store.objects.append,
        on_replace=store.objects.replace,
        on_get_many=store.objects.get_many,
        on_scan=store.objects.scan,
    )

    groups = GroupService(
        on_get=store.objects.get,
        on_append=store.objects.append,
        on_replace=store.objects.replace,
        on_get_many=store.objects.get_many,
        on_scan=store.objects.scan,
    )

    join_svc = JoinService(
        on_get=store.objects.get,
        on_append=store.objects.append,
        on_replace=store.objects.replace,
        on_get_many=store.objects.get_many,
        on_scan=store.objects.scan,
    )

    accounts = AccountService(
        on_append=store.objects.append,
        on_replace=store.objects.replace,
        on_get_by_key=store.objects.get,
        on_scan=store.objects.scan,
    )

    permgrant = PermissionGrantService(
        on_get=store.objects.get,
        on_append=store.objects.append,
        on_replace=store.objects.replace,
        on_get_many=store.objects.get_many,
        on_scan=store.objects.scan,
    )

    verifier = AllowAllSecretVerifier()

    async def on_after_verify(*, user) -> dict:
        return {}

    auth = AuthenticationService(
        on_get_user=users.get_by_username,
        on_verify_user=verifier.verify,
        on_after_verify=on_after_verify,
    )

    await bootstrap(
        users=users,
        groups=groups,
        join_svc=join_svc,
        permgrant=permgrant,
    )

    await _demo_data(users=users)

    ports.promote("ident.users", users)
    ports.promote("ident.namespaces", service_ns)
    ports.promote("ident.groups", groups)
    ports.promote("ident.joins", join_svc)
    ports.promote("ident.permgrant", permgrant)


async def _build_index(store):
    namespaces = Namespaces()
    await store.objects.ensure_indexes(
        namespace=namespaces.user_namespace(),
        specs=UserService.index_specs(),
    )
    await store.objects.ensure_indexes(
        namespace=namespaces.group_namespace(),
        specs=GroupService.index_specs(),
    )
    await store.objects.ensure_indexes(
        namespace=namespaces.join_namespace(),
        specs=JoinService.index_specs(),
    )
    await store.objects.ensure_indexes(
        namespace=namespaces.permgrant_namespace(),
        specs=PermissionGrantService.index_specs(),
    )


async def _demo_data(users) -> None:
    namespaces = Namespaces()
    user_ns = namespaces.user_namespace()

    u1 = User(
        key=Key(namespace=user_ns, id="stefan"),
        data=UserData(username="stefan", password_hash="123"),
    )
    await users.save(u1)

    u2 = User(
        key=Key(namespace=user_ns, id="lara"),
        data=UserData(username="lara", password_hash="456"),
    )
    await users.save(u2)
