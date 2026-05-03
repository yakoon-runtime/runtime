from yakoon.base.application import Application
from yakoon.base.naming import Namespace
from yakoon.base.naming.key import Key
from yakoon.base.plugins import ModulePorts
from yakoon.base.plugins.ports import OnAuthenticate
from yakoon.ident.models.account import Account, AccountData
from yakoon.storage.eventstore import StoreRuntime, build_memory_store

from .controllers import BaseController
from .services import AccountService, AllowAllSecretVerifier, AuthenticationService


class IdentityApp(Application):

    id: str = "ident-app"
    name = "ident"

    controllers = (BaseController,)

    store: StoreRuntime
    auth: AuthenticationService
    accounts: AccountService

    def on_build(self, ports: ModulePorts) -> None:

        # ----------------------
        # --- BUILDING STORE ---
        # ----------------------

        self.store = build_memory_store()

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

        # ------------------------
        # --- CREATING ACCOUNT ---
        # ------------------------

        self.auth = AuthenticationService(
            on_get_account=self.accounts.get_by_username,
            on_verify_account=verifier.verify,
        )

        # ------------------
        # --- PUBLISHING ---
        # ------------------

        ports.on_publish(OnAuthenticate, self.auth.authenticate)

    # ----------------------------
    # --- LIFECYCLE - ON_START ---
    # ----------------------------

    async def on_start(self, ports: ModulePorts) -> None:

        await self._build_index()
        await self._demo_data()

    # -------------------
    # --- BUILD INDEX ---
    # -------------------

    async def _build_index(self):
        from .services.account import IDX_ACCOUNT_USERNAME_SPEC

        await self.store.objects.ensure(
            namespace=Namespace("system", "account", "develop"),
            specs=[
                IDX_ACCOUNT_USERNAME_SPEC,
            ],
        )

    # ----------------
    # --- DEMODATA ---
    # ----------------

    async def _demo_data(self, space: str = "develop") -> None:

        ns = Namespace(domain="system", kind="account", space=space)

        a1 = Account(
            AccountData(
                Key(namespace=ns, id="1"),
                username="stefan",
                password_hash="123",
                roles=["admin"],
            )
        )
        await self.accounts.save(a1)

        a2 = Account(
            AccountData(
                Key(namespace=ns, id="2"),
                username="lara",
                password_hash="456",
                roles=["user"],
            )
        )
        await self.accounts.save(a2)
