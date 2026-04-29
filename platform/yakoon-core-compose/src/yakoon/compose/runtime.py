from typing import Literal, TypeAlias

from yakoon.base import ports
from yakoon.base.application import Application
from yakoon.base.capabilities.identity import PermissionService
from yakoon.base.capabilities.interaction import FieldPolicy, FieldPolicyEngine
from yakoon.base.naming import Namespace
from yakoon.base.plugins.container import ModulePorts
from yakoon.base.plugins.ports import (
    OnListCommandsForApp,
    OnListCommandsForManual,
    OnProject,
    OnSaveSession,
)
from yakoon.base.projection.model import FieldType
from yakoon.base.runtime import Container
from yakoon.base.sources import OnDataSource
from yakoon.platform.capabilities.audit.service import DefaultAuditLogService
from yakoon.platform.capabilities.identity.services.permission_service import (
    DefaultPermissionService,
)
from yakoon.platform.machine.host import RuntimeHost
from yakoon.platform.machine.wire import build_machine
from yakoon.platform.plugins import PluginLoader
from yakoon.platform.projection import (
    build_projector,
    build_stream,
)
from yakoon.platform.runtime import EntityStoreSessionService
from yakoon.platform.sources.data import (
    AppSource,
    CommandQueryBuilder,
)
from yakoon.platform.sources.registry import DataSourceRegistry
from yakoon.platform.stores.event.backends.memory import MemoryBackend
from yakoon.platform.stores.event.batches.json_patch import JsonPatchStrategy
from yakoon.platform.stores.event.store import DefaultEntityStore

CapabilityMode: TypeAlias = Literal["default"]
CapabilitySelection: TypeAlias = dict[str, CapabilityMode | None]


def compose_runtime(
    bootstrap: Container,
    *,
    plugins: list[str] | None = None,
    capabilities: CapabilitySelection | None = None,
) -> RuntimeHost:

    plugins = plugins or []
    capabilities = capabilities or {}

    store = _compose_store()

    # ----------------
    # --- SERVICES ---
    # ----------------

    session_service = EntityStoreSessionService(store)
    permission_service = DefaultPermissionService()
    audit_service = DefaultAuditLogService()

    # ----------------
    # --- PLUGINS ---
    # ----------------

    plug_loader = PluginLoader(
        plugins=plugins,
        capabilities=capabilities,
    )

    applications: list[Application] = []
    for module in plug_loader.load():
        if module.export.app:
            applications.append(module.export.app())

    # -----------------
    # --- PROJECTOR ---
    # -----------------

    projector = build_projector()

    # --------------------
    # --- DATASOURCING ---
    # --------------------

    ds = DataSourceRegistry()
    ds.bind("system:apps", AppSource(applications))
    ds.bind(
        "system:commands",
        CommandQueryBuilder(
            applications=applications,
            on_has_read_permission=permission_service.can_read,
        ),
    )

    # ----------------
    # --- QUERYING ---
    # ----------------

    command_query = CommandQueryBuilder(
        applications=applications,
        on_has_read_permission=permission_service.can_read,
    )

    # ----------------
    # --- BINDINGS ---
    # ----------------

    def bind_ports() -> ModulePorts:
        ports = bootstrap.fork()

        ports.bind(OnDataSource, ds.read)
        ports.bind(OnSaveSession, session_service.save)
        ports.bind(OnProject, projector.project)

        ports.bind(OnListCommandsForApp, command_query.for_app)
        ports.bind(OnListCommandsForManual, command_query.for_man_entries)

        return ModulePorts(
            on_register=ports.bind,
            on_get_port=ports.get,
        )

    for app in applications:
        app.bind_ports(bind_ports())

    _compose_ports(
        bootstrap,
        store,
    )

    # _compose_permission_roles(bootstrap)
    # _compose_policies(bootstrap)

    # --- STREAMING ---

    output = build_stream()

    # --- MACHINE HANDLING ---

    return build_machine(
        applications=applications,
        c_query=command_query,
        on_session=session_service.get_or_create,
        on_projection=output.send_projection,
        on_has_exec_permission=permission_service.can_execute,
        on_bootstrap_permissions=permission_service.set_bootstrap_permissions,
        on_audit_log=audit_service.audit,
        on_audit_error=audit_service.error,
        on_audit_security=audit_service.security,
        on_audit_warning=audit_service.warning,
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
) -> Container:

    # register event store.
    container.bind(ports.EntityStore, store)
    container.bind(ports.IndexRegistry, store)

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
