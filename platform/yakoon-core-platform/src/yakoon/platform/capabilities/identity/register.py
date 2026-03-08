from typing import Any

from yakoon.base.capabilities.identity import (
    AccountService,
    AuthenticationService,
    PermissionService,
    SecretVerifier,
)
from yakoon.base.plugins import ModuleExport, ModuleMeta
from yakoon.base.runtime.services import ServiceDirectory

from . import (
    AuthCoreController,
    DefaultAccountService,
    DefaultAllowAllSecretVerifier,
    DefaultAuthenticationService,
    DefaultPermissionService,
)

meta = ModuleMeta(
    name="yakoon.identity",
    version="0.1.0",
    description="Identity...",
)


def register(services: ServiceDirectory) -> ModuleExport:

    public_services: list[type] = []

    # provide: internal module service (not exported to platform)
    def provide(port_type: type[Any], instance: Any) -> None:
        services.register_static(port_type, instance)

    # publish: public capability port exported to the platform
    def publish(port_type: type, instance: object) -> None:
        provide(port_type, instance)
        public_services.append(port_type)

    provide(SecretVerifier, DefaultAllowAllSecretVerifier())

    publish(AccountService, DefaultAccountService(services))
    publish(AuthenticationService, DefaultAuthenticationService(services))
    publish(PermissionService, DefaultPermissionService())

    return ModuleExport(
        meta,
        controllers=[
            AuthCoreController,
        ],
        public_services=public_services,
    )
