from yakoon.base import ports
from yakoon.base.capabilities.audit import AuditLogService
from yakoon.base.capabilities.identity import (
    AccountService,
    AuthenticationService,
    PermissionService,
    SecretVerifier,
)
from yakoon.base.capabilities.interaction import (
    DialogService,
    FieldPolicy,
    InputService,
    PolicyService,
)
from yakoon.base.capabilities.presenters import PresenterService
from yakoon.base.catalogs import (
    CommandCatalog,
    CommandCatalogService,
    CommandInfo,
    ControllerCatalog,
    ControllerCatalogService,
    ControllerInfo,
)
from yakoon.base.engine import CommandQueueService
from yakoon.base.ids import NamespaceService
from yakoon.base.runtime.controllers import Controller
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.runtime.sessions.port import SessionService
from yakoon.base.ui import FieldType, ViewSpecParser
from yakoon.base.values import Namespace
from yakoon.platform.capabilities.audit import DefaultAuditLogService
from yakoon.platform.capabilities.identity import (
    DefaultAccountService,
    DefaultAuthenticationService,
    DefaultPermissionService,
    DefaultZeroSecretVerifier,
)
from yakoon.platform.capabilities.interaction import (
    DefaultDialogService,
    DefaultInputService,
    DefaultPolicyService,
)
from yakoon.platform.capabilities.presenters import DefaultPresenterService
from yakoon.platform.catalogs import (
    DefaultCommandCatalogService,
    DefaultControllerCatalogService,
)
from yakoon.platform.engine import (
    CommandDirectory,
    CommandEngine,
    ControllerDirectory,
    DefaultCommandQueueService,
)
from yakoon.platform.ids import DefaultNamespaceService
from yakoon.platform.plugins.manager import PluginManager
from yakoon.platform.plugins.registry import PluginRegistry
from yakoon.platform.runtime import DefaultSessionService
from yakoon.platform.runtime.render.jinja.engine import JinjaRenderer
from yakoon.platform.services.file import FileLoader
from yakoon.platform.services.lookup import NoLookupResolverService
from yakoon.platform.services.render import RendererService
from yakoon.platform.services.stream import OutputStreamService
from yakoon.platform.stores.event.backends.memory import MemoryBackend
from yakoon.platform.stores.event.batches.json_patch import JsonPatchStrategy
from yakoon.platform.stores.event.store import DefaultEntityStore
from yakoon.platform.ui import DefaultViewSpecParser


def compose_engine(*, plugins: list[str]) -> CommandEngine:
    directory = ControllerDirectory()

    bootstrap = ServiceDirectory()
    bootstrap.register_static(ports.PluginRegistry, PluginRegistry())

    loaded = PluginManager(bootstrap).load(plugins)

    controllers: list[Controller] = []
    for lp in loaded:
        # export.public_services are registered globally (root service directory)
        for port_type in lp.export.public_services:
            bootstrap.register_static(port_type, lp.services.get(port_type))

        # controllers are instantiated and connected to the plugin's service directory
        for controller_type in lp.export.controllers:
            ctrl = controller_type()
            ctrl.connect_services(lp.services)
            controllers.append(ctrl)

    directory.register(controllers)

    command_catalog = _compose_command_catalog(directory)
    controller_catalog = _compose_controller_catalog(directory)
    commands = _compose_commands(bootstrap, directory)
    store = _compose_store()

    _compose_services(
        bootstrap,
        store,
        controller_catalog,
        command_catalog,
    )

    _compose_permission_roles(bootstrap)
    _compose_policies(bootstrap)

    commands.validate()

    return CommandEngine(directory, bootstrap, commands)


def _compose_permission_roles(services: ServiceDirectory):
    permissions = services.get(PermissionService)
    permissions.register_role(
        "admin",
        [
            "auth:su|rx",
            "shell:use|rx",
            "office.mailing:sendmail|rx",
        ],
    )
    permissions.register_role(
        "user",
        [
            "shell:use|rx",
        ],
    )


def _compose_policies(services: ServiceDirectory):
    policy = services.get(PolicyService)
    policy.register_defaults()
    policy.register_policies(
        [
            FieldPolicy(
                key="customer.first_name",
                type=FieldType.STRING,
                required=False,
            ),
            FieldPolicy(
                key="customer.age",
                hint="mit hint",
                type=FieldType.INT,
                required=False,
            ),
            FieldPolicy(
                key="auth.password",
                hint="kein Echo",
                type=FieldType.STRING,
                secret=True,
            ),
        ]
    )


def _compose_controller_catalog(directory: ControllerDirectory) -> ControllerCatalog:
    controllers_list: list[ControllerInfo] = []
    for controller in directory.get_all():
        controllers_list.append(
            ControllerInfo(
                controller.id,
                controller.is_shell,
                controller.is_activatable,
                controller.is_listed,
                controller.resources.clone(),
            )
        )
    return ControllerCatalog(controllers_list)


def _compose_command_catalog(directory: ControllerDirectory) -> CommandCatalog:
    command_list: list[CommandInfo] = []
    for controller in directory.get_all():
        for sets in controller.commandsets:
            for command in sets.commands():
                command_list.append(
                    CommandInfo(
                        command.key,
                        command.kind,
                        command.scope,
                        command.visibility,
                        controller.id,
                        sets.group,
                    )
                )
    return CommandCatalog(command_list)


def _compose_commands(
    services: ServiceDirectory, directory: ControllerDirectory
) -> CommandDirectory:
    commands = CommandDirectory(services)
    for controller in directory.get_all():
        commands.register(controller.id, controller.commandsets)

    return commands


def _compose_services(
    services: ServiceDirectory,
    store: DefaultEntityStore,
    controller_catalog: ControllerCatalog,
    command_catalog: CommandCatalog,
) -> ServiceDirectory:

    # core platform services
    services.register_static(AuditLogService, DefaultAuditLogService())
    services.register_static(NamespaceService, DefaultNamespaceService())
    services.register_static(SessionService, DefaultSessionService(store))
    services.register_static(CommandQueueService, DefaultCommandQueueService())
    services.register_static(PresenterService, DefaultPresenterService(services))
    services.register_static(AccountService, DefaultAccountService(store))
    services.register_static(SecretVerifier, DefaultZeroSecretVerifier())
    services.register_static(PermissionService, DefaultPermissionService())
    services.register_static(DialogService, DefaultDialogService())
    services.register_static(PolicyService, DefaultPolicyService())
    services.register_static(InputService, DefaultInputService(services))
    services.register_static(ViewSpecParser, DefaultViewSpecParser())
    services.register_static(ports.FileLoader, FileLoader())
    services.register_static(ports.RendererService, RendererService(services))
    services.register_static(ports.RenderEngine, JinjaRenderer())
    services.register_static(ports.OutputStreamService, OutputStreamService())

    services.register_static(
        AuthenticationService, DefaultAuthenticationService(services)
    )

    # register event store.
    services.register_static(ports.EntityStore, store)
    services.register_static(ports.IndexRegistry, store)

    # optional lookup feature (can be overridden by plugin export.public_services)
    if not services.has(ports.LookupResolverService):
        services.register_static(ports.LookupResolverService, NoLookupResolverService())

    # counters / sharding
    # services.register_static(
    #    ports.ShardedCounterService,
    #    ShardedCounterService(ShardAllocator(stores.counters)),
    # )

    # catalogs (info-only surface)
    services.register_static(
        ControllerCatalogService,
        DefaultControllerCatalogService(controller_catalog),
    )
    services.register_static(
        CommandCatalogService,
        DefaultCommandCatalogService(services, command_catalog),
    )

    services.get(CommandCatalogService).build()

    return services


def _compose_store() -> DefaultEntityStore:

    backend = MemoryBackend()
    patch = JsonPatchStrategy(max_ops=50)

    store = DefaultEntityStore(
        backend=backend,
        writer=patch,
        readers={
            patch.format: patch,
        },
        # snapshot_policy=..., enable_revisions=True
    )

    return store


async def initialize_storage(services: ServiceDirectory) -> None:
    index = services.get(ports.IndexRegistry)

    from yakoon.platform.capabilities.identity.account_service import (
        IDX_ACCOUNT_USERNAME_SPEC,
    )

    await index.ensure(
        namespace=Namespace("system", "account", "develop"),
        specs=[
            IDX_ACCOUNT_USERNAME_SPEC,
        ],
    )
