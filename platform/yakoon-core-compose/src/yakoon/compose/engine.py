from typing import Literal, TypeAlias

from yakoon.base import ports
from yakoon.base.application import Application
from yakoon.base.capabilities.discovery import LookupResolver
from yakoon.base.capabilities.identity import PermissionService
from yakoon.base.capabilities.interaction import FieldPolicy, FieldPolicyEngine
from yakoon.base.dispatch import CommandQueue
from yakoon.base.naming import Namespace, NamespaceResolver
from yakoon.base.plugins import ModuleImport
from yakoon.base.projection.model import FieldType
from yakoon.base.projection.percept import ProjectionDispatcher
from yakoon.base.projection.transfer import Output
from yakoon.base.runtime import Container
from yakoon.base.runtime.sessions import SessionStore
from yakoon.platform.capabilities.audit.service import DefaultAuditLogService
from yakoon.platform.capabilities.identity.services.permission_service import (
    DefaultPermissionService,
)
from yakoon.platform.catalogs import (
    AppQueryBuilder,
    CommandQueryBuilder,
)
from yakoon.platform.machine import (
    InMemoryCommandQueue,
)
from yakoon.platform.machine.host import RuntimeHost
from yakoon.platform.machine.wire import build_machine
from yakoon.platform.naming import DomainNamespaceResolver
from yakoon.platform.plugins.wire import load_modules
from yakoon.platform.projection import (
    EventProjectionDispatcher,
)
from yakoon.platform.projection.transport import EventStreamOutput
from yakoon.platform.projection.wire import build_projector
from yakoon.platform.runtime import EntityStoreSessionService
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

    permission_service = DefaultPermissionService()
    audit_service = DefaultAuditLogService()

    projector = build_projector()

    module_imports = ModuleImport(on_project=projector.project)
    modules = load_modules(module_imports, plugins, capabilities)

    apps: list[Application] = []
    for module in modules:
        if module.export.app:
            apps.append(module.export.app)

    apps_query = AppQueryBuilder(apps)
    command_query = CommandQueryBuilder(
        app_query=apps_query,
        on_has_read_permission=permission_service.can_read,
    )

    store = _compose_store()

    _compose_ports(
        bootstrap,
        store,
        apps_query,
    )

    # _compose_permission_roles(bootstrap)
    # _compose_policies(bootstrap)

    return build_machine(
        a_query=apps_query,
        c_query=command_query,
        on_has_exec_permission=permission_service.can_execute,
        on_bootstrap_permissions=permission_service.set_bootstrap_permissions,
        on_get_applications=apps_query.all,
        on_audit_log=audit_service.audit,
        on_audit_error=audit_service.error,
        on_audit_security=audit_service.security,
        on_audit_warning=audit_service.warning,
        container=bootstrap,
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

    container.register_static(ProjectionDispatcher, EventProjectionDispatcher())
    container.register_static(Output, EventStreamOutput())

    # register event store.
    container.register_static(ports.EntityStore, store)
    container.register_static(ports.IndexRegistry, store)

    # optional lookup feature (can be overridden by plugin export.public_services)
    if not container.has(LookupResolver):
        container.register_static(LookupResolver, NoLookupResolver())

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
