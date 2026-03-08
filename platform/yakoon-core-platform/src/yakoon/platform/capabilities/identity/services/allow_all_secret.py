from yakoon.base.capabilities.identity import Account


class DefaultAllowAllSecretVerifier:

    def verify(self, account: Account, secret: str) -> bool:
        return account.password_hash == secret
