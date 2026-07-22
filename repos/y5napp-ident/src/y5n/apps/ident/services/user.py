from __future__ import annotations

from y5n.runtime.api.naming import Key, Namespace
from y5nstore.event.models import (
    IndexKey,
    IndexSpec,
    IndexTerm,
    SnapshotHint,
    ValueType,
)
from y5nstore.event.ports import (
    OnAppend,
    OnGet,
    OnGetMany,
    OnReplace,
    OnScan,
)

from ..models import User, UserData

# ----------------------------------
# INDEX
# ----------------------------------

IDX_USER_USERNAME_KEY = IndexKey("user.username")
IDX_USER_USERNAME_SPEC = IndexSpec(
    key=IDX_USER_USERNAME_KEY,
    value_type=ValueType.TEXT,
    unique=True,
)

# ----------------------------------
# SERVICE
# ----------------------------------


class UserService:

    @staticmethod
    def index_specs():
        return [IDX_USER_USERNAME_SPEC]

    def __init__(
        self,
        on_get: OnGet,
        on_append: OnAppend,
        on_replace: OnReplace,
        on_get_many: OnGetMany,
        on_scan: OnScan,
    ):
        self.on_get = on_get
        self.on_append = on_append
        self.on_replace = on_replace
        self.on_get_many = on_get_many
        self.on_scan = on_scan

    async def get_by_key(self, key: Key) -> User | None:
        row = await self.on_get(key=key)
        if not row.ok:
            return None

        return User.from_row(row=row)

    async def get_by_username(self, namespace: Namespace, username: str) -> User | None:

        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_USER_USERNAME_KEY,
            value=username,
            limit=1,
        )

        if not keys:
            return None

        row = await self.on_get(key=keys[0])
        if not row.ok:
            return None

        return User.from_row(row=row)

    async def save(self, user: User) -> None:
        doc = user.data.to_dict()

        username = doc.get("username")
        if not isinstance(username, str):
            raise TypeError("User.username must be a string")

        await self.on_replace(
            key=user.key,
            doc=doc,
            indexes=[IndexTerm(key=IDX_USER_USERNAME_KEY, value=username)],
            snapshot_hint=SnapshotHint.COMMIT,
        )

    async def list_users(self, namespace: Namespace) -> list[User]:
        keys, _ = await self.on_scan(
            namespace=namespace,
            index_key=IDX_USER_USERNAME_KEY,
        )

        rows = await self.on_get_many(keys=keys)
        users = [User.from_row(row) for row in rows if row.ok]

        return [u for u in users if u.data.enabled]

    async def add_user(
        self,
        *,
        namespace: Namespace,
        username: str,
        password: str | None = None,
    ) -> User:
        key = Key(namespace=namespace, id=username)

        existing = await self.get_by_key(key)
        if existing:
            raise ValueError(f"User already exists: {username}")

        user = User(
            key=key,
            data=UserData(
                username=username,
                password_hash=password,
            ),
        )

        await self.save(user)
        return user

    async def edit_user(
        self,
        *,
        namespace: Namespace,
        username: str,
        changes: dict,
    ) -> User:
        user = await self.get_by_username(namespace, username)
        if not user:
            raise ValueError(f"User not found: {username}")

        password = changes.get("password")
        if password is not None:
            user.data.password_hash = password

        enabled = changes.get("enabled")
        if enabled is not None:
            user.data.enabled = enabled

        await self.save(user)
        return user

    async def delete_user(
        self,
        *,
        namespace: Namespace,
        username: str,
    ) -> None:
        user = await self.get_by_username(namespace, username)
        if not user:
            raise ValueError(f"User not found: {username}")

        user.data.enabled = False
        await self.save(user)
