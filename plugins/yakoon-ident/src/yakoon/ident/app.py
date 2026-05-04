from yakoon.base.application import Application
from yakoon.base.naming import Namespace
from yakoon.base.naming.key import Key
from yakoon.base.plugins import ModulePorts
from yakoon.base.plugins.ports import OnAuthenticate
from yakoon.storage.eventstore import StoreRuntime
from yakoon.storage.eventstore.wire import build_store

from .controllers import BaseController
from .models import User, UserData
from .services import (
    AccountService,
    AllowAllSecretVerifier,
    AuthenticationService,
    UserService,
)
from .settings import Settings


class IdentityApp(Application):

    id: str = "ident-app"
    name = "ident"

    controllers = (BaseController,)

    store: StoreRuntime
    auth: AuthenticationService
    accounts: AccountService
    users: UserService

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
            on_store=self.store.objects.put,
            on_replace=self.store.objects.replace,
            on_get_by_key=self.store.objects.get_one,
            on_find=self.store.objects.scan,
        )

        # -------------------------------
        # --- CREATING ACCOUNT ACCESS ---
        # -------------------------------

        self.accounts = AccountService(
            on_store=self.store.objects.put,
            on_replace=self.store.objects.replace,
            on_get_by_key=self.store.objects.get_one,
            on_find=self.store.objects.scan,
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

        await self.store.objects.ensure(
            namespace=Namespace("system", "user", "global"),
            specs=UserService.index_specs(),
        )

    # ----------------
    # --- DEMODATA ---
    # ----------------

    async def _demo_data(self) -> None:

        user_ns = Namespace(domain="system", kind="user", space="global")

        u1 = User(
            UserData(
                key=Key(namespace=user_ns, id="stefan"),
                username="stefan",
                password_hash="123",
            )
        )
        await self.users.save(u1)

        u2 = User(
            UserData(
                key=Key(namespace=user_ns, id="lara"),
                username="lara",
                password_hash="456",
            )
        )
        await self.users.save(u2)
