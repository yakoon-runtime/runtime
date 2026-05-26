from typing import Protocol

from ...models.group import Group
from ...models.user import User

# ----------------------------------
# MEMBERSHIP
# ----------------------------------


class OnResolveSubject(Protocol):
    async def __call__(self, subject_type: str, subject_name: str) -> User | Group: ...
