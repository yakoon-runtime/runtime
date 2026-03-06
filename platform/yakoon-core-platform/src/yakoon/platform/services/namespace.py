from yakoon.base.runtime import Session
from yakoon.base.values.namespace import Namespace


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
