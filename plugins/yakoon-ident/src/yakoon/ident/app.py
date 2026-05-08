from yakoon.base.application import Application
from yakoon.base.naming.key import Key
from yakoon.base.plugins import ModulePorts
from yakoon.base.plugins.ports import OnAuthenticate
from yakoon.storage.eventstore import StoreRuntime
from yakoon.storage.eventstore.wire import build_store

from .controllers import AdminController, AuthController
from .models import User, UserData
from .services import (
    AccountService,
    AllowAllSecretVerifier,
    AuthenticationService,
    GroupService,
    IdentityNamespaces,
    MembershipService,
    PermissionGrantService,
    UserService,
)
from .settings import Settings


class IdentityApp(Application):

    id: str = "ident-app"
    name = "ident"

    controllers = (
        AuthController,
        AdminController,
    )

    store: StoreRuntime
    auth: AuthenticationService
    accounts: AccountService
    users: UserService
    groups: GroupService
    membership: MembershipService
    permgrant: PermissionGrantService

    def on_build(self, ports: ModulePorts) -> None:

        settings = Settings()

        # ----------------------
        # --- BUILDING STORE ---
        # ----------------------

        self.store = build_store(settings.storage)

        # -------------------------------
        # --- CREATING USER ACCESS ---
        # -------------------------------

        self.users = UserService(
            on_get=self.store.objects.get,
            on_append=self.store.objects.append,
            on_replace=self.store.objects.replace,
            on_get_many=self.store.objects.get_many,
            on_scan=self.store.objects.scan,
        )
        # -------------------------------
        # --- CREATING GROUP ACCESS ---
        # -------------------------------

        self.groups = GroupService(
            on_get=self.store.objects.get,
            on_append=self.store.objects.append,
            on_replace=self.store.objects.replace,
            on_get_many=self.store.objects.get_many,
            on_scan=self.store.objects.scan,
        )

        # --------------------------
        # --- CREATING MS ACCESS ---
        # --------------------------

        self.membership = MembershipService(
            on_get=self.store.objects.get,
            on_append=self.store.objects.append,
            on_replace=self.store.objects.replace,
            on_get_many=self.store.objects.get_many,
            on_scan=self.store.objects.scan,
        )

        # -------------------------------
        # --- CREATING ACCOUNT ACCESS ---
        # -------------------------------

        self.accounts = AccountService(
            on_append=self.store.objects.append,
            on_replace=self.store.objects.replace,
            on_get_by_key=self.store.objects.get,
            on_scan=self.store.objects.scan,
        )

        self.permgrant = PermissionGrantService(
            on_get=self.store.objects.get,
            on_append=self.store.objects.append,
            on_replace=self.store.objects.replace,
            on_get_many=self.store.objects.get_many,
            on_scan=self.store.objects.scan,
        )

        # ---------------------------
        # --- ALLOW ALL PASSWORDS ---
        # ---------------------------

        verifier = AllowAllSecretVerifier()

        # ----------------------
        # --- AUTHENTICATING ---
        # ----------------------

        self.auth = AuthenticationService(
            on_get_user=self.users.get_by_username,
            on_verify_user=verifier.verify,
        )

        # ------------------
        # --- PUBLISHING ---
        # ------------------

        ports.on_publish(OnAuthenticate, self.auth.authenticate)

        # -----------------------
        # --- PROVIDE INTENAL ---
        # -----------------------

        ports.on_provide(UserService, self.users)
        ports.on_provide(GroupService, self.groups)
        ports.on_provide(MembershipService, self.membership)
        ports.on_provide(PermissionGrantService, self.permgrant)

    # ----------------------------
    # --- LIFECYCLE - ON_START ---
    # ----------------------------

    async def on_start(self, ports: ModulePorts) -> None:

        await self.store.initialize()

        await self._build_index()
        await self._demo_data()

    # -------------------
    # --- BUILD INDEX ---
    # -------------------

    async def _build_index(self):

        namespaces = IdentityNamespaces()

        await self.store.objects.ensure_indexes(
            namespace=namespaces.user_namespace(),
            specs=UserService.index_specs(),
        )
        await self.store.objects.ensure_indexes(
            namespace=namespaces.group_namespace(),
            specs=GroupService.index_specs(),
        )
        await self.store.objects.ensure_indexes(
            namespace=namespaces.membership_namespace(),
            specs=MembershipService.index_specs(),
        )
        await self.store.objects.ensure_indexes(
            namespace=namespaces.permgrant_namespace(),
            specs=PermissionGrantService.index_specs(),
        )

    # ----------------
    # --- DEMODATA ---
    # ----------------

    async def _demo_data(self) -> None:

        namespaces = IdentityNamespaces()
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
