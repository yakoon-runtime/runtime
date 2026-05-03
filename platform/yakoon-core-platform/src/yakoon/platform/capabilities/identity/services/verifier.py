from yakoon.base.capabilities.identity import Account


class AllowAllSecretVerifier:

    def verify(self, account: Account, secret: str) -> bool:
        return account.password_hash == secret
