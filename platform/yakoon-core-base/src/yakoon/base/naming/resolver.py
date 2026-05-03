from .namespace import Namespace


class NamespaceResolver:

    _domain: str = "System"

    def __init__(self, domain: str | None = None):
        self._domain = domain or self._domain

    def from_session(self, session, kind: str, space: str | None) -> Namespace:
        return Namespace(
            domain=session.key.namespace.domain,
            kind=kind,
            space=space or session.key.namespace.space,
        )
