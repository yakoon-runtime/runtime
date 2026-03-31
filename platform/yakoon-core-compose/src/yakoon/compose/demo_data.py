from __future__ import annotations

from yakoon.base.capabilities.identity import Account, AccountData, AccountService
from yakoon.base.naming import Key, Namespace
from yakoon.base.runtime import Container


async def seed_demo_system_data(
    container: Container, *, space: str = "develop"
) -> None:

    accounts = container.get(AccountService)
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
