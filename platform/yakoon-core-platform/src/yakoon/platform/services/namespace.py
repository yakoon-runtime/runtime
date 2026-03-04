from yakoon.base.models.ns import Namespace
from yakoon.base.runtime.session import Session


class NamespaceService:

    _domain: str = "yakoon"

    def __init__(self, domain: str | None = None):
        self._domain = domain or self._domain

    async def from_session(
        self, session: Session, kind: str, space: str | None
    ) -> Namespace:
        return Namespace(
            domain=session.key.namespace.domain,
            kind=kind,
            space=space or session.key.namespace.space,
        )
