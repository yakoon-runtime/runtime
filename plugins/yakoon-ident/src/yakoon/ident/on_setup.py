from __future__ import annotations

from yakoon.base.naming.key import Key
from yakoon.base.nodes import RuntimeContext
from yakoon.base.plugins.ports import OnAuthenticate
from yakoon.ident.models.user import User, UserData
from yakoon.ident.services.authentication import AuthenticationService
from yakoon.ident.services.verifier import AllowAllSecretVerifier
from yakoon.platform.capabilities.permission import PermissionParser
from yakoon.storage.eventstore.wire import build_store

from .services import (
    AccountService,
    GroupService,
    MembershipService,
    Namespaces,
    PermissionGrantService,
    PermissionResolver,
    UserService,
)
from .settings import Settings

# ----------------------------------
# COMMAND
# ----------------------------------


async def on_setup(ctx: RuntimeContext):

    settings = Settings()

    # -------------------
    # --- NAMESPACING ---
    # -------------------

    namespaces = Namespaces()

    # ----------------------
    # --- BUILDING STORE ---
    # ----------------------

    store = build_store(settings.storage)
    await _build_index(store)

    # -------------------------------
    # --- CREATING USER ACCESS ---
    # -------------------------------

    users = UserService(
        on_get=store.objects.get,
        on_append=store.objects.append,
        on_replace=store.objects.replace,
        on_get_many=store.objects.get_many,
        on_scan=store.objects.scan,
    )

    # -------------------------------
    # --- CREATING GROUP ACCESS ---
    # -------------------------------

    groups = GroupService(
        on_get=store.objects.get,
        on_append=store.objects.append,
        on_replace=store.objects.replace,
        on_get_many=store.objects.get_many,
        on_scan=store.objects.scan,
    )

    # --------------------------
    # --- CREATING MS ACCESS ---
    # --------------------------

    membership = MembershipService(
        on_get=store.objects.get,
        on_append=store.objects.append,
        on_replace=store.objects.replace,
        on_get_many=store.objects.get_many,
        on_scan=store.objects.scan,
    )

    # -------------------------------
    # --- CREATING ACCOUNT ACCESS ---
    # -------------------------------

    accounts = AccountService(
        on_append=store.objects.append,
        on_replace=store.objects.replace,
        on_get_by_key=store.objects.get,
        on_scan=store.objects.scan,
    )

    # -----------------------------
    # --- CREATING GRANT ACCESS ---
    # -----------------------------

    permgrant = PermissionGrantService(
        on_get=store.objects.get,
        on_append=store.objects.append,
        on_replace=store.objects.replace,
        on_get_many=store.objects.get_many,
        on_scan=store.objects.scan,
    )

    # -------------------------------
    # --- CREATING PERM RESOLVER ---
    # -------------------------------

    perm_parser = PermissionParser()
    perm_resolver = PermissionResolver(
        on_list_subject_grants=permgrant.list_subject_grants,
        on_list_user_memberships=membership.list_user_memberships,
        on_parse_spec=perm_parser.parse,
    )

    # ---------------------------
    # --- ALLOW ALL PASSWORDS ---
    # ---------------------------

    verifier = AllowAllSecretVerifier()

    # ----------------------
    # --- AUTHENTICATING ---
    # ----------------------

    auth = AuthenticationService(
        on_get_user=users.get_by_username,
        on_verify_user=verifier.verify,
    )

    # ------------------
    # --- PUBLISHING ---
    # ------------------

    ctx.ports.publish(OnAuthenticate, auth.authenticate)

    # -----------------------
    # --- PROVIDE INTENAL ---
    # -----------------------

    # await IdentityBootstrapper(
    #    users=users,
    #    groups=groups,
    #    membership=membership,
    #    permgrant=permgrant,
    # ).bootstrap()

    # await _demo_data()

    # ------------------------
    # --- PROVIDE INTERNAL ---
    # ------------------------

    ctx.ports.provide(Namespaces, namespaces)
    ctx.ports.provide(UserService, users)
    ctx.ports.provide(GroupService, groups)
    ctx.ports.provide(MembershipService, membership)
    ctx.ports.provide(PermissionGrantService, permgrant)
    ctx.ports.provide(PermissionResolver, perm_resolver)


# ----------------------------------
# BUILD INDEX
# ----------------------------------


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
        namespace=namespaces.membership_namespace(),
        specs=MembershipService.index_specs(),
    )
    await store.objects.ensure_indexes(
        namespace=namespaces.permgrant_namespace(),
        specs=PermissionGrantService.index_specs(),
    )


# ----------------
# --- DEMODATA ---
# ----------------


async def _demo_data(self) -> None:

    namespaces = Namespaces()
    user_ns = namespaces.user_namespace()

    u1 = User(
        key=Key(namespace=user_ns, id="stefan"),
        data=UserData(
            username="stefan",
            password_hash="123",
        ),
    )
    await self.users.save(u1)

    u2 = User(
        key=Key(namespace=user_ns, id="lara"),
        data=UserData(
            username="lara",
            password_hash="456",
        ),
    )
    await self.users.save(u2)
