from __future__ import annotations

from yakoon.base import ports
from yakoon.base.models.account import Account, AccountData
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.values.key import Key
from yakoon.base.values.namespace import Namespace


async def seed_demo_system_data(
    services: ServiceDirectory, *, space: str = "develop"
) -> None:

    accounts = services.get(ports.AccountService)
    ns = Namespace(domain="system", kind="account", space=space)

    a1 = Account(
        AccountData(
            Key(namespace=ns, id="1"),
            username="stefan",
            password_hash="123",
            roles=["admin"],
        )
    )
    await accounts.save(a1)

    a2 = Account(
        AccountData(
            Key(namespace=ns, id="2"),
            username="lara",
            password_hash="456",
            roles=["user"],
        )
    )
    await accounts.save(a2)
