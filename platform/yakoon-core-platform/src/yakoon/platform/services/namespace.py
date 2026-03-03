from yakoon.base.models.ns import Namespace
from yakoon.base.runtime.session import Session


class NamespaceService:

    _domain: str = "yakoon"

    def __init__(self, domain: str = None):
        self._domain = domain or self._domain

    async def from_session(self, session: Session) -> Namespace:
        return Namespace(
            domain=self._domain,
            kind="bucket",
            space="develop",
        )

    async def get_by_bucket(
        self, bucket: str = "bucket", scope: str = "develop"
    ) -> Namespace:
        return Namespace(self._domain, bucket, scope)
