from __future__ import annotations

from y5n.api.naming import Key
from y5n.api.nodes import NodeSpace
from y5n.api.ports import (
    AUTHENTICATE,
    OnNewPermissionSet,
    OnParsePermissionSpec,
)
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
    PermissionResolver,
    UserService,
)
from .settings import Settings


async def run(space: NodeSpace):

    settings = Settings()

    namespaces = Namespaces()

    store = build_store(settings.storage)
    await _build_index(store)

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

    on_new_permset = space.ports.get(OnNewPermissionSet)
    on_parse_spec = space.ports.get(OnParsePermissionSpec)
    perm_resolver = PermissionResolver(
        on_new_permissionset=on_new_permset,
        on_list_subject_grants=permgrant.list_subject_grants,
        on_list_user_joins=join_svc.list_user_joins,
        on_parse_spec=on_parse_spec,
    )

    verifier = AllowAllSecretVerifier()

    auth = AuthenticationService(
        on_get_user=users.get_by_username,
        on_verify_user=verifier.verify,
    )

    space.ports.publish(AUTHENTICATE, auth.authenticate)

    await bootstrap(
        users=users,
        groups=groups,
        join_svc=join_svc,
        permgrant=permgrant,
    )

    await _demo_data(users=users)

    space.ports.provide(Namespaces, namespaces)
    space.ports.provide(UserService, users)
    space.ports.provide(GroupService, groups)
    space.ports.provide(JoinService, join_svc)
    space.ports.provide(PermissionGrantService, permgrant)
    space.ports.provide(PermissionResolver, perm_resolver)


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
        data=UserData(
            username="stefan",
            password_hash="123",
        ),
    )
    await users.save(u1)

    u2 = User(
        key=Key(namespace=user_ns, id="lara"),
        data=UserData(
            username="lara",
            password_hash="456",
        ),
    )
    await users.save(u2)
