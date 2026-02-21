from yakoon.base.commands.command import Command
from yakoon.base.commands.request import Request
from yakoon.base.ports import (
    AuthenticationService,
    NamespaceService,
    PermissionService,
    SessionService,
)
from yakoon.base.runtime.session import Session


class CmdSu(Command):

    key = "su"

    async def run(self, session: Session, request: Request) -> None:  # noqa: ARG002

        presenter = await self.get_presenter(session)
        auth = self.services.get(AuthenticationService)
        namespaces = self.services.get(NamespaceService)
        permissions = self.services.get(PermissionService)

        ns = await namespaces.from_session(session)

        username = (
            request.arg(0)
            or request.option("user")
            or (await presenter.inputs.ask("ask_user")).first()
        )
        secret = request.option("password")
        if not secret:
            secret = (await presenter.inputs.ask("ask_secret")).first()
            if secret:
                secret = secret.reveal()

        result = await auth.authenticate(ns, username, secret)
        if result.ok and result.account:
            account = result.account
            session.set_identity(account.key, account.username)
            permissions.apply_account_permissions(session, account)

            await self.services.get(SessionService).save(session)
            await presenter.views.emit("success", user=username)

        else:
            await presenter.views.emit("failed", user=username, reason=result.reason)
