from typing import Literal, TypeAlias

from yakoon.base import ports
from yakoon.base.application import Application
from yakoon.base.capabilities.audit.port import AuditLogService
from yakoon.base.capabilities.discovery import LookupResolver
from yakoon.base.capabilities.identity import PermissionService
from yakoon.base.capabilities.interaction import FieldPolicy, FieldPolicyEngine
from yakoon.base.catalogs import (
    AppInfo,
    ApplicationQuery,
    CommandInfo,
    CommandQuery,
    ControllerInfo,
)
from yakoon.base.dispatch import CommandQueue
from yakoon.base.naming import Namespace, NamespaceResolver
from yakoon.base.plugins import ModuleRegistry
from yakoon.base.plugins.module import LoadedModule
from yakoon.base.projection import ProjectorFactory
from yakoon.base.projection.compiler import ProjectionCompiler
from yakoon.base.projection.model import FieldType
from yakoon.base.projection.percept import ProjectionDispatcher
from yakoon.base.projection.rendering import ProjectionRenderer, RenderEngine
from yakoon.base.projection.transfer import Output
from yakoon.base.resources import ResourceLoader
from yakoon.base.runtime import Container
from yakoon.base.runtime.sessions import SessionStore
from yakoon.platform.catalogs import (
    AppQueryBuilder,
    CommandQueryBuilder,
)
from yakoon.platform.machine import (
    CommandEngine,
    CommandResolver,
    InMemoryCommandQueue,
)
from yakoon.platform.machine.host import RuntimeHost
from yakoon.platform.machine.runner import RunnerFactory
from yakoon.platform.machine.scheduler import Scheduler
from yakoon.platform.naming import DomainNamespaceResolver
from yakoon.platform.plugins import DefaultModuleManager, DefaultModuleRegistry
from yakoon.platform.projection import (
    EventProjectionDispatcher,
    TemplateProjectionCompiler,
    TemplateProjectorFactory,
)
from yakoon.platform.projection.rendering import (
    JinjaRenderEngine,
    TemplateProjectionRenderer,
)
from yakoon.platform.projection.transport import EventStreamOutput
from yakoon.platform.resources import FileResourceLoader
from yakoon.platform.runtime import EntityStoreSessionService
from yakoon.platform.runtime.bus.session_bus import SessionBus
from yakoon.platform.services.lookup import NoLookupResolver
from yakoon.platform.stores.event.backends.memory import MemoryBackend
from yakoon.platform.stores.event.batches.json_patch import JsonPatchStrategy
from yakoon.platform.stores.event.store import DefaultEntityStore

CapabilityMode: TypeAlias = Literal["default"]
CapabilitySelection: TypeAlias = dict[str, CapabilityMode | None]


def compose_engine(
    bootstrap: Container,
    *,
    plugins: list[str] | None = None,
    capabilities: CapabilitySelection | None = None,
) -> RuntimeHost:

    plugins = plugins or []
    capabilities = capabilities or {}

    bootstrap.register_static(ModuleRegistry, DefaultModuleRegistry())
    manager = DefaultModuleManager(
        bootstrap,
        capability_prefix="yakoon.platform.capabilities",
    )

    loaded: list[LoadedModule] = []
    loaded.extend(manager.load_capabilities(capabilities))
    loaded.extend(manager.load_modules(plugins))

    app_types: dict[AppInfo, type[Application]] = {}
    app_infos: list[AppInfo] = []
    for lm in loaded:

        for port_type in lm.export.public_ports:
            bootstrap.register_static(port_type, lm.container.get(port_type))

        app_type = lm.export.app
        if app_type:

            app_info = build_app_infos(app_type, lm.container)
            app_types[app_info] = app_type
            app_infos.append(app_info)

    apps_query = AppQueryBuilder(app_infos)

    store = _compose_store()

    _compose_ports(
        bootstrap,
        store,
        apps_query,
    )

    _compose_permission_roles(bootstrap)
    _compose_policies(bootstrap)

    # fetch global servcies
    command_query = bootstrap.get(CommandQuery)
    permissions = bootstrap.get(PermissionService)
    session_service = bootstrap.get(SessionStore)
    audit = bootstrap.get(AuditLogService)
    output = bootstrap.get(Output)

    # build resolver
    resolver = CommandResolver(command_query)
    for app_info in apps_query.all():
        application = app_types[app_info]
        for controller in application.controllers:
            resolver.register(controller)

    # create command engine
    engine = CommandEngine(
        apps=apps_query,
        resolver=resolver,
        permissions=permissions,
        auditlogs=audit,
        output=output,
    )

    # build scheduler
    scheduler = Scheduler(engine, audit, output)

    # create runner factory.
    global_commands = {cmd.key for cmd in command_query.globals()}
    runner_factory = RunnerFactory(engine, scheduler, global_commands)

    # compose runtime host.
    return RuntimeHost(
        scheduler=scheduler,
        runner=runner_factory,
        bus=SessionBus(),
        session_service=session_service,
        permission_service=permissions,
    )


def _compose_permission_roles(container: Container):
    permissions = container.get(PermissionService)
    permissions.register_role(
        "admin",
        [
            "app-app:su|rx",
            "shell-app:use|rx",
            "office.mailing:sendmail|rx",
        ],
    )
    permissions.register_role(
        "user",
        [
            "shell-app:use|rx",
        ],
    )


def build_app_infos(app: type[Application], app_context: Container) -> AppInfo:

    controller_infos: list[ControllerInfo] = []
    for controller in app.controllers:

        controller.container = app_context

        command_infos: list[CommandInfo] = []
        for commandset in controller.commandsets:
            for command in commandset.commands:
                command_infos.append(
                    CommandInfo(
                        key=command.key,
                        app_id=app.id,
                        controller_id=controller.id,
                        kind=command.kind,
                        scope=command.scope,
                        visibility=command.visibility,
                        category=commandset.group,
                    )
                )

        controller_infos.append(
            ControllerInfo(
                id=controller.id,
                is_shell=controller.is_shell,
                is_listed=controller.is_listed,
                is_activatable=controller.is_activatable,
                resources=controller.resources.clone(),
                commands=tuple(command_infos),
            )
        )

    return AppInfo(
        id=app.id,
        is_shell=app.is_shell,
        is_listed=app.is_listed,
        is_activatable=app.is_activatable,
        controllers=tuple(controller_infos),
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


def _compose_ports(
    container: Container,
    store: DefaultEntityStore,
    directory: AppQueryBuilder,
) -> Container:

    # core platform
    container.register_static(NamespaceResolver, DomainNamespaceResolver())
    container.register_static(SessionStore, EntityStoreSessionService(store))
    container.register_static(CommandQueue, InMemoryCommandQueue())
    container.register_static(ResourceLoader, FileResourceLoader())
    container.register_static(RenderEngine, JinjaRenderEngine())

    container.register_static(ProjectorFactory, TemplateProjectorFactory(container))
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

    container.register_static(ApplicationQuery, directory)

    permissions = container.get(PermissionService)
    container.register_static(
        CommandQuery,
        CommandQueryBuilder(directory, permissions),
    )

    container.get(CommandQuery).build()

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
