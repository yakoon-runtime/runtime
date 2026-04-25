from yakoon.base.plugins import ModuleExport, ModuleImport, ModuleMeta

from .app import AuthApplication

meta = ModuleMeta(
    name="yakoon.identity",
    version="0.1.0",
    description="Identity...",
)


def register(ports: ModuleImport) -> ModuleExport:

    # provide(SecretVerifier, DefaultAllowAllSecretVerifier())

    # publish(AccountService, DefaultAccountService(container))
    # publish(AuthenticationService, DefaultAuthenticationService(container))
    # publish(PermissionService, DefaultPermissionService())

    return ModuleExport(
        meta,
        app=AuthApplication(
            platform_ports=ports,
        ),
    )
