from typing import Literal, TypeAlias

from yakoon.base import ports
from yakoon.base.capabilities.discovery import LookupResolver
from yakoon.base.capabilities.identity import PermissionService
from yakoon.base.capabilities.interaction import FieldPolicy, FieldPolicyEngine
from yakoon.base.catalogs import (
    CommandCatalog,
    CommandInfo,
    CommandRegistry,
    ControllerCatalog,
    ControllerInfo,
    ControllerRegistry,
)
from yakoon.base.controllers import Controller
from yakoon.base.dispatch import CommandQueue
from yakoon.base.naming import Namespace, NamespaceResolver
from yakoon.base.plugins import ModuleRegistry
from yakoon.base.projection import ProjectionParser, ProjectorFactory
from yakoon.base.projection.compiler import ProjectionCompiler
from yakoon.base.projection.model import FieldType
from yakoon.base.projection.percept import ProjectionDispatcher
from yakoon.base.projection.rendering import ProjectionRenderer, RenderEngine
from yakoon.base.projection.transport import Output
from yakoon.base.resources import ResourceLoader
from yakoon.base.runtime import Container
from yakoon.base.runtime.sessions import SessionStore
from yakoon.platform.catalogs import (
    CommandIndexBuilder,
    ControllerIndexBuilder,
)
from yakoon.platform.machine import (
    CommandDirectory,
    CommandEngine,
    ControllerDirectory,
    InMemoryCommandQueue,
)
from yakoon.platform.naming import DomainNamespaceResolver
from yakoon.platform.plugins import DefaultModuleManager, DefaultModuleRegistry
from yakoon.platform.projection import (
    EventProjectionDispatcher,
    TemplateProjectorFactory,
    YamlProjectionParser,
)
from yakoon.platform.projection.compiler import TemplateProjectionCompiler
from yakoon.platform.projection.rendering import (
    JinjaRenderEngine,
    TemplateProjectionRenderer,
)
from yakoon.platform.projection.transport import EventStreamOutput
from yakoon.platform.resources import FileResourceLoader
from yakoon.platform.runtime import EntityStoreSessionService
from yakoon.platform.services.lookup import NoLookupResolver
from yakoon.platform.stores.event.backends.memory import MemoryBackend
from yakoon.platform.stores.event.batches.json_patch import JsonPatchStrategy
from yakoon.platform.stores.event.store import DefaultEntityStore

CapabilityMode: TypeAlias = Literal["default"]
CapabilitySelection: TypeAlias = dict[str, CapabilityMode | None]


def compose_engine(
    *,
    plugins: list[str] | None = None,
    capabilities: CapabilitySelection | None = None,
) -> CommandEngine:
    plugins = plugins or []
    capabilities = capabilities or {}

    directory = ControllerDirectory()

    bootstrap = Container()
    bootstrap.register_static(ModuleRegistry, DefaultModuleRegistry())

    manager = DefaultModuleManager(
        bootstrap,
        capability_prefix="yakoon.platform.capabilities",
    )

    loaded = []
    loaded.extend(manager.load_capabilities(capabilities))
    loaded.extend(manager.load_modules(plugins))

    controllers: list[Controller] = []
    for lm in loaded:
        for port_type in lm.export.public_ports:
            bootstrap.register_static(port_type, lm.container.get(port_type))

        for controller_type in lm.export.controllers:
            ctrl = controller_type()
            ctrl.set_container(lm.container)
            controllers.append(ctrl)

    directory.register(controllers)

    command_catalog = _compose_command_catalog(directory)
    controller_catalog = _compose_controller_catalog(directory)
    commands = _compose_commands(bootstrap, directory)
    store = _compose_store()

    _compose_ports(
        bootstrap,
        store,
        controller_catalog,
        command_catalog,
    )

    _compose_permission_roles(bootstrap)
    _compose_policies(bootstrap)

    commands.validate()

    return CommandEngine(directory, bootstrap, commands)


def _compose_permission_roles(container: Container):
    permissions = container.get(PermissionService)
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


def _compose_policies(container: Container):
    policy = container.get(FieldPolicyEngine)
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
    container: Container, directory: ControllerDirectory
) -> CommandDirectory:
    commands = CommandDirectory(container)
    for controller in directory.get_all():
        commands.register(controller.id, controller.commandsets)

    return commands


def _compose_ports(
    container: Container,
    store: DefaultEntityStore,
    controller_catalog: ControllerCatalog,
    command_catalog: CommandCatalog,
) -> Container:

    # core platform
    container.register_static(NamespaceResolver, DomainNamespaceResolver())
    container.register_static(SessionStore, EntityStoreSessionService(store))
    container.register_static(CommandQueue, InMemoryCommandQueue())
    container.register_static(ResourceLoader, FileResourceLoader())
    container.register_static(RenderEngine, JinjaRenderEngine())

    container.register_static(ProjectorFactory, TemplateProjectorFactory(container))
    container.register_static(ProjectionParser, YamlProjectionParser())
    container.register_static(ProjectionRenderer, TemplateProjectionRenderer(container))
    container.register_static(ProjectionCompiler, TemplateProjectionCompiler())

    container.register_static(ProjectionDispatcher, EventProjectionDispatcher())
    container.register_static(Output, EventStreamOutput())

    # register event store.
    container.register_static(ports.EntityStore, store)
    container.register_static(ports.IndexRegistry, store)

    # optional lookup feature (can be overridden by plugin export.public_services)
    if not container.has(LookupResolver):
        container.register_static(LookupResolver, NoLookupResolver())

    # counters / sharding
    # services.register_static(
    #    ports.ShardedCounterService,
    #    ShardedCounterService(ShardAllocator(stores.counters)),
    # )

    # catalogs (info-only surface)
    container.register_static(
        ControllerRegistry,
        ControllerIndexBuilder(controller_catalog),
    )
    container.register_static(
        CommandRegistry,
        CommandIndexBuilder(container, command_catalog),
    )

    container.get(CommandRegistry).build()

    return container


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


async def initialize_storage(container: Container) -> None:
    index = container.get(ports.IndexRegistry)

    from yakoon.platform.capabilities.identity.services.account_service import (
        IDX_ACCOUNT_USERNAME_SPEC,
    )

    await index.ensure(
        namespace=Namespace("system", "account", "develop"),
        specs=[
            IDX_ACCOUNT_USERNAME_SPEC,
        ],
    )
