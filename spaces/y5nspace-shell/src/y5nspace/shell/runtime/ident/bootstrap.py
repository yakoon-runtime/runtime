from y5n.api.naming import Key

from ...models.ident import (
    Group,
    GroupData,
    Membership,
    MembershipData,
    PermissionGrant,
    PermissionGrantData,
    User,
    UserData,
)
from ...services.ident import (
    GroupService,
    MembershipService,
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
    "ident-app:membership|rwx",
    "ident-app:membership.add|rwx",
    "ident-app:membership.remove|rwx",
    "ident-app:membership.groups|rwx",
    "ident-app:membership.users|rwx",
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
    membership: MembershipService,
    permgrant: PermissionGrantService,
) -> None:

    namespaces = Namespaces()

    user_ns = namespaces.user_namespace()
    group_ns = namespaces.group_namespace()
    membership_ns = namespaces.membership_namespace()
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

    membership_key = Membership.build_key(
        namespace=membership_ns,
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

    if not await membership.get_by_key(membership_key):

        await membership.save(
            Membership(
                key=membership_key,
                data=MembershipData(
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
