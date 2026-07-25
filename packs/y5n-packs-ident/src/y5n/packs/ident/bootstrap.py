from y5n.runtime.api.naming import Key

from .models import (
    Group,
    GroupData,
    Join,
    JoinData,
    PermissionGrant,
    PermissionGrantData,
    User,
    UserData,
)
from .services import (
    GroupService,
    JoinService,
    Namespaces,
    PermissionGrantService,
    UserService,
)

_root_grant_specs = [
    # ident - user
    "ident-app:user|rwx",
    "ident-app:user.list|rwx",
    "ident-app:user.add|rwx",
    "ident-app:user.edit|rwx",
    "ident-app:user.delete|rwx",
    # ident - group
    "ident-app:group|rwx",
    "ident-app:group.list|rwx",
    "ident-app:group.add|rwx",
    "ident-app:group.edit|rwx",
    "ident-app:group.delete|rwx",
    # ident - member
    "ident-app:join|rwx",
    "ident-app:join.add|rwx",
    "ident-app:join.remove|rwx",
    "ident-app:join.groups|rwx",
    "ident-app:join.users|rwx",
    # ident - grant
    "ident-app:grant|rwx",
    "ident-app:grant.add|rwx",
    "ident-app:grant.remove|rwx",
    "ident-app:grant.user|rwx",
    "ident-app:grant.group|rwx",
    "ident-app:grant.permission|rwx",
]


async def bootstrap(
    users: UserService,
    groups: GroupService,
    join_svc: JoinService,
    permgrant: PermissionGrantService,
) -> None:

    namespaces = Namespaces()

    user_ns = namespaces.user_namespace()
    group_ns = namespaces.group_namespace()
    join_ns = namespaces.join_namespace()
    grant_ns = namespaces.permgrant_namespace()

    # -------------------
    # --- ROOT / ADMIN ---
    # -------------------

    root_key = Key(
        namespace=user_ns,
        id="root",
    )

    admins_key = Key(
        namespace=group_ns,
        id="admins",
    )

    join_key = Join.build_key(
        namespace=join_ns,
        user_key=root_key,
        group_key=admins_key,
    )

    # ----------------------
    # --- ROOT USER ---
    # ----------------------

    if not await users.get_by_key(root_key):

        await users.save(
            User(
                key=root_key,
                data=UserData(
                    username="root",
                    password_hash="master",
                ),
            )
        )

    # -----------------------
    # --- ADMINS GROUP ---
    # -----------------------

    if not await groups.get_by_key(admins_key):

        await groups.save(
            Group(
                key=admins_key,
                data=GroupData(
                    name="admins",
                ),
            )
        )

    # -----------------------
    # --- ROOT MEMBERSHIP ---
    # -----------------------

    if not await join_svc.get_by_key(join_key):

        await join_svc.save(
            Join(
                key=join_key,
                data=JoinData(
                    user_key=root_key,
                    group_key=admins_key,
                ),
            )
        )

    # -------------------
    # --- ROOT GRANTS ---
    # -------------------

    for spec in _root_grant_specs:

        grant_key = PermissionGrant.build_key(
            namespace=grant_ns,
            subject_key=admins_key,
            permission_key=spec,
        )

        if await permgrant.get_by_key(grant_key):
            continue

        await permgrant.save(
            PermissionGrant(
                key=grant_key,
                data=PermissionGrantData(
                    subject_key=admins_key,
                    permission_key=spec,
                ),
            )
        )
