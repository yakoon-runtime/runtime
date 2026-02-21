
from yakoon.base.models.account import Account, AccountData
from yakoon.base.models.key import Key
from yakoon.base.models.ns import Namespace
from yakoon.base.stores.base.base_store import BaseStore


class AccountService:
    """
    Loads/saves accounts via a dict-based store.

    The store persists plain dict rows. This service maps them to AccountData
    and returns Account façades to callers.
    """

    def __init__(self, store: BaseStore):
        self.store = store

    async def get_by_key(self, key: Key) -> Account | None:
        row = await self.store.get_by_key(key)
        if not row:
            return None
        data = AccountData.from_dict(row)
        return Account(data)

    async def get_by_username(
        self, namespace: Namespace, username: str
    ) -> Account | None:
        rows = await self.store.fetch_by_fields(
            namespace=namespace, username=username, limit=1
        )
        if not rows:
            return None
        data = AccountData.from_dict(rows[0])
        return Account(data)

    async def save(self, account: Account) -> None:
        row = account.data.to_dict()
        await self.store.save(row)

    async def delete_by_key(self, key: Key) -> None:
        await self.store.delete_by_key(key)
