"""Python projections of Runtime API Port contracts.

A Runtime API port is identified by its dotted name on the Runtime Bus
(``Call(port, method, args)`` — the wire contract stays language-neutral).
The Protocols in this module are the Python SDK projection of those
contracts: typing information for ``ports.get(name, Contract)``. They are
never transmitted, registered, inspected or validated by the Runtime —
any provider implementation may satisfy them structurally.
"""

from typing import Protocol


class IdentAuth(Protocol):
    """Contract of the Runtime API port ``ident.auth``.

    Authenticates credentials against the identity domain and, on
    success, updates the caller's session identity, security context
    and permissions.
    """

    async def authenticate(
        self,
        *,
        username: str,
        secret: str,
        security_context: str = "normal",
    ) -> dict: ...
