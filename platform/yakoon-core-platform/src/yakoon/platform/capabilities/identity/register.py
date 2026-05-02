from yakoon.base.plugins import ModuleExport, ModuleMeta

from .app import IdentityApp

meta = ModuleMeta(
    name="yakoon.identity",
    version="0.1.0",
    description="Identity...",
)


def register() -> ModuleExport:

    # provide(SecretVerifier, DefaultAllowAllSecretVerifier())

    # publish(AccountService, DefaultAccountService(container))
    # publish(AuthenticationService, DefaultAuthenticationService(container))
    # publish(PermissionService, DefaultPermissionService())

    return ModuleExport(
        meta,
        app=IdentityApp,
    )
