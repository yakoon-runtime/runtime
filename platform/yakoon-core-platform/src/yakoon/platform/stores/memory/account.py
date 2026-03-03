from yakoon.base.models.account import Account, AccountData
from yakoon.base.models.key import Key
from yakoon.base.models.ns import Namespace
from yakoon.base.stores.memory.base_store import MemoryStore


class InMemoryAccountStore(MemoryStore):
    """
    Domain-specific store for BaseSession objects.
    Currently uses raw MemoryStore behavior.
    Override methods here only if session-specific logic is required.
    """

    def __init__(self):
        super().__init__()
        load_defaults(self)

    def add(self, account: Account):
        self._rows[str(account.key)] = account.data.to_dict()


def load_defaults(store: InMemoryAccountStore):

    ns = Namespace(domain="yakoon", kind="bucket", space="develop")

    data = AccountData(
        Key(namespace=ns, id="1"),
        username="stefan",
        password_hash="123",
        roles=["admin"],
    )

    store.add(Account(data))

    data = AccountData(
        Key(namespace=ns, id="2"), username="lara", password_hash="456", roles=["user"]
    )

    store.add(Account(data))
