import hashlib

from ...models.ident import User


class AllowAllSecretVerifier:

    def verify(self, user: User, secret: str) -> bool:
        return user.data.password_hash == secret


class SimpleHashVerifier:

    def verify(self, user: User, secret: str) -> bool:
        hashed = hashlib.sha256(secret.encode()).hexdigest()
        return user.data.password_hash == hashed
