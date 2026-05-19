from yakoon.base.plugins import ModuleExport, ModuleMeta

from .app import IdentityApp


def register() -> ModuleExport:

    # provide(SecretVerifier, DefaultAllowAllSecretVerifier())

    # publish(AccountService, DefaultAccountService(container))
    # publish(AuthenticationService, DefaultAuthenticationService(container))
    # publish(PermissionService, DefaultPermissionService())

    return ModuleExport(
        node=None,
        meta=ModuleMeta(
            name="yakoon.ident",
            version="0.1.0",
            description="Identity...",
        ),
    )
