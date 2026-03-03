from yakoon.base import ports
from yakoon.base.controllers.base import BaseController
from yakoon.base.directories.service import ServiceDirectory
from yakoon.base.models.catalog import CommandInfo, ControllerInfo
from yakoon.base.models.fields import FieldType
from yakoon.base.models.policy import FieldPolicy
from yakoon.base.stores.base.registry import StoreRegistry
from yakoon.base.stores.batches.json_patch import JsonPatchStrategy
from yakoon.base.stores.event.entity import PluginGroup, ScopeId
from yakoon.platform.directories.controller import ControllerDirectory
from yakoon.platform.engines.command.engine import Engine
from yakoon.platform.engines.command.router import CommandDirectory
from yakoon.platform.plugins.manager import PluginManager
from yakoon.platform.plugins.registry import PluginRegistry
from yakoon.platform.runtime.render.jinja.engine import JinjaRenderer
from yakoon.platform.services.account import AccountService
from yakoon.platform.services.auditlog import AuditLogService
from yakoon.platform.services.auth import AuthenticationService, ZeroSecretVerifier
from yakoon.platform.services.catalog import (
    CommandCatalog,
    CommandCatalogService,
    ControllerCatalog,
    ControllerCatalogService,
)
from yakoon.platform.services.dialog import DialogService
from yakoon.platform.services.file import FileLoader
from yakoon.platform.services.input import InputService
from yakoon.platform.services.lookup import NoLookupResolverService
from yakoon.platform.services.namespace import NamespaceService
from yakoon.platform.services.perm import PermissionService
from yakoon.platform.services.policy import PolicyService
from yakoon.platform.services.presenter import PresenterService
from yakoon.platform.services.queue import CommandQueueService
from yakoon.platform.services.render import RendererService
from yakoon.platform.services.session import SessionService
from yakoon.platform.services.shard import ShardAllocator, ShardedCounterService
from yakoon.platform.services.stream import OutputStreamService
from yakoon.platform.services.viewspec import ViewSpecService
from yakoon.platform.stores.event.backend_memory import MemoryBackend
from yakoon.platform.stores.event.store import DefaultEntityStore
from yakoon.platform.stores.factory import create_system_stores


def compose_engine(*, plugin_modules: list[str]) -> Engine:
    directory = ControllerDirectory()

    bootstrap = ServiceDirectory()
    bootstrap.register_static(ports.PluginRegistry, PluginRegistry())

    loaded = PluginManager(bootstrap).load(plugin_modules)

    controllers: list[BaseController] = []
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
        create_system_stores("memory", db_path="db/gateway.sqlite3.db"),
        controller_catalog,
        command_catalog,
    )

    _compose_permission_roles(bootstrap)
    _compose_policies(bootstrap)

    commands.validate()

    return Engine(directory, bootstrap, commands)


def _compose_permission_roles(services: ServiceDirectory):
    permissions = services.get(ports.PermissionService)
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
    policy = services.get(ports.PolicyService)
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
    stores: StoreRegistry,
    controller_catalog: ControllerCatalog,
    command_catalog: CommandCatalog,
) -> ServiceDirectory:

    # core platform services
    services.register_static(ports.AuditLogService, AuditLogService())
    services.register_static(ports.NamespaceService, NamespaceService())
    services.register_static(ports.SessionService, SessionService(store))
    services.register_static(ports.CommandQueueService, CommandQueueService())
    services.register_static(ports.PresenterService, PresenterService(services))
    services.register_static(ports.AccountService, AccountService(store))
    services.register_static(ports.SecretVerifier, ZeroSecretVerifier())
    services.register_static(ports.PermissionService, PermissionService())
    services.register_static(ports.DialogService, DialogService())
    services.register_static(ports.PolicyService, PolicyService())
    services.register_static(ports.InputService, InputService(services))
    services.register_static(ports.ViewSpecService, ViewSpecService())
    services.register_static(ports.FileLoader, FileLoader())
    services.register_static(ports.RendererService, RendererService(services))
    services.register_static(ports.RenderEngine, JinjaRenderer())
    services.register_static(ports.OutputStreamService, OutputStreamService())

    services.register_static(
        ports.AuthenticationService, AuthenticationService(services)
    )

    # register event store.
    services.register_static(ports.EntityStore, store)
    services.register_static(ports.IndexRegistry, store)

    # optional lookup feature (can be overridden by plugin export.public_services)
    if not services.has(ports.LookupResolverService):
        services.register_static(ports.LookupResolverService, NoLookupResolverService())

    # counters / sharding
    services.register_static(
        ports.ShardedCounterService,
        ShardedCounterService(ShardAllocator(stores.counters)),
    )

    # catalogs (info-only surface)
    services.register_static(
        ports.ControllerCatalogService,
        ControllerCatalogService(controller_catalog),
    )
    services.register_static(
        ports.CommandCatalogService,
        CommandCatalogService(services, command_catalog),
    )

    services.get(ports.CommandCatalogService).build()

    return services


def _compose_store() -> DefaultEntityStore:

    backend = MemoryBackend()
    patch = JsonPatchStrategy(max_ops=50)

    store = DefaultEntityStore(
        backend=backend,
        patch_strategy=patch,
        # snapshot_policy=..., enable_revisions=True
    )

    return store


async def initialize_storage(services: ServiceDirectory, *, scope: str) -> None:
    index = services.get(ports.IndexRegistry)

    from yakoon.platform.services.account import IDX_ACCOUNT_USERNAME_SPEC

    await index.ensure(
        scope_id=ScopeId(scope),
        plugin_group=PluginGroup("system"),
        specs=[
            IDX_ACCOUNT_USERNAME_SPEC,
        ],
    )
