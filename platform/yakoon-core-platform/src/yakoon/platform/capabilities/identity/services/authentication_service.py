from yakoon.base.capabilities.identity import AccountService, AuthResult, SecretVerifier
from yakoon.base.naming import Namespace
from yakoon.base.runtime import Container


class DefaultAuthenticationService:

    def __init__(self, container: Container):
        self._container = container

    async def authenticate(
        self, namespace: Namespace, username: str, secret: str
    ) -> AuthResult:

        accounts = self._container.get(AccountService)
        verifier = self._container.get(SecretVerifier)

        acc = await accounts.get_by_username(namespace, username)
        if not acc:
            return AuthResult(ok=False, reason="unknown-user")

        if not verifier.verify(acc, secret):
            return AuthResult(ok=False, reason="invalid-credentials")

        return AuthResult(ok=True, account=acc)
