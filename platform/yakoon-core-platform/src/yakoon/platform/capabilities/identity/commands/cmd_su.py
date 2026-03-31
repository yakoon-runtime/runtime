from yakoon.base.capabilities.identity import AuthenticationService, PermissionService
from yakoon.base.commands import Command, Request
from yakoon.base.naming import NamespaceResolver
from yakoon.base.runtime.sessions import SessionStore


class CmdSu(Command):

    key = "su"

    async def run(self, request: Request) -> None:  # noqa: ARG002

        projector = await self.create_projector(session)
        auth = self.container.get(AuthenticationService)
        namespaces = self.container.get(NamespaceResolver)
        permissions = self.container.get(PermissionService)

        # TODO: Woher bekommt ein Plugin einen stabilen Namespace?
        ns = await namespaces.from_session(session, "account", "develop")

        username = (
            request.arg(0)
            or request.option("user")
            or (await projector.require_first("ask_user"))
        )
        secret = request.option("password")
        if not secret:
            secret = await projector.require_first("ask_secret")
            if secret:
                secret = secret.reveal()

        result = await auth.authenticate(ns, username, secret)
        if result.ok and result.account:
            account = result.account
            session.set_identity(account.key, account.username)
            permissions.apply_account_permissions(session, account)

            await self.container.get(SessionStore).save(session)
            await projector.project(
                "success",
                state={
                    "user": username,
                },
            )

        else:
            await projector.project(
                "failed",
                state={
                    "user": username,
                    "reason": result.reason,
                },
            )
