from typing import Literal, TypeAlias

from yakoon.base.application import Application
from yakoon.base.nodes import Node as AppContainer
from yakoon.base.plugins import ModulePorts
from yakoon.base.plugins.ports import (
    OnAuthorizeRead,
    OnAuthorizeWrite,
    OnManualGet,
    OnManualRegister,
    OnProject,
    OnProjectionRegister,
    OnSaveSession,
)
from yakoon.base.runtime import Container
from yakoon.base.sources import OnDataSource
from yakoon.platform.capabilities.audit import AuditLogService
from yakoon.platform.capabilities.permission import (
    PermissionChecker,
)
from yakoon.platform.machine.host import RuntimeHost
from yakoon.platform.machine.wire import build_machine
from yakoon.platform.manual import ManualService
from yakoon.platform.plugins import PluginLoader
from yakoon.platform.projection import (
    build_projector,
    build_stream,
)
from yakoon.platform.resources import ProjectionRegistry
from yakoon.platform.runtime.sessions import SessionService
from yakoon.platform.services import GuidanceService
from yakoon.platform.settings import Settings
from yakoon.platform.sources.data import (
    AppSource,
    CommandSource,
    DiscoverySource,
)
from yakoon.platform.sources.registry import DataSourceRegistry
from yakoon.platform.templates.wire import register_templates
from yakoon.storage.eventstore.wire import build_store

CapabilityMode: TypeAlias = Literal["default"]
CapabilitySelection: TypeAlias = dict[str, CapabilityMode | None]


def compose_runtime(
    *,
    plugins: list[str] | None = None,
    capabilities: CapabilitySelection | None = None,
    settings: Settings,
) -> RuntimeHost:

    ports = Container()

    plugins = plugins or []
    capabilities = capabilities or {}
    nodes: list[AppContainer] = []

    # -------------------
    # --- PROJECTIONS ---
    # -------------------

    projections = ProjectionRegistry()
    register_templates(projections.register)

    # ----------------------
    # --- BUILDING STORE ---
    # ----------------------

    store = build_store(settings.storage)

    # ---------------
    # --- MANUALS ---
    # ---------------

    manuals = ManualService()

    # ----------------
    # --- SERVICES ---
    # ----------------

    guidance_service = GuidanceService()

    session_manager = SessionService(
        on_replace=store.objects.replace,
        on_get=store.objects.get,
    )

    audit_service = AuditLogService(settings.logging)

    # -------------------
    # --- PERMISSIONS ---
    # -------------------

    perm_checker = PermissionChecker()

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
            if module.export.node:
                nodes.append(module.export.node)

    # -----------------
    # --- PROJECTOR ---
    # -----------------

    projector = build_projector(
        on_resource=projections.resolve,
    )

    # --------------------
    # --- DATASOURCING ---
    # --------------------

    ds = DataSourceRegistry()
    ds.bind("system:apps", AppSource(applications))
    ds.bind("system:commands", CommandSource(applications))
    ds.bind("system:discovery", DiscoverySource(ds.read, perm_checker.can_read))

    # ----------------
    # --- BINDINGS ---
    # ----------------

    def bind_ports() -> ModulePorts:

        fork = ports.fork()

        fork.bind(OnDataSource, ds.read)
        fork.bind(OnProject, projector.project)
        fork.bind(OnSaveSession, session_manager.save)
        fork.bind(OnAuthorizeRead, perm_checker.can_read)
        fork.bind(OnAuthorizeWrite, perm_checker.can_write)
        fork.bind(OnProjectionRegister, projections.register)
        fork.bind(OnManualRegister, manuals.register)
        fork.bind(OnManualGet, manuals.get)

        return ModulePorts(
            on_publish=ports.bind,
            on_provide=fork.bind,
            on_get_port=fork.get,
        )

    for app in applications:
        app.initialize()
        app.bind_ports(bind_ports())

    # -----------------
    # --- STREAMING ---
    # -----------------

    output = build_stream()

    # --------------------
    # --- INITIALIZING ---
    # --------------------

    async def initialize():
        await store.initialize()
        await build_index()

    # -------------------
    # --- BUILD INDEX ---
    # -------------------

    async def build_index():
        pass

    # ------------------------
    # --- MACHINE HANDLING ---
    # ------------------------

    return build_machine(
        nodes=nodes,
        on_suggest=guidance_service.suggest,
        on_session=session_manager.get_or_create,
        on_projection=output.send_projection,
        on_has_permission=perm_checker.can_execute,
        on_audit_log=audit_service.audit,
        on_audit_error=audit_service.error,
        on_audit_security=audit_service.security,
        on_audit_warning=audit_service.warning,
        on_load_projection=projector.project,
        on_initialize=initialize,
    )


# def _compose_policies(c):
#     policy = "get(FieldPolicyEngine)"
#     policy.register_defaults()
#     policy.register_policies(
#         [
#             FieldPolicy(
#                 key="customer.first_name",
#                 type=FieldType.STRING,
#                 required=False,
#             ),
#             FieldPolicy(
#                 key="customer.age",
#                 hint="mit hint",
#                 type=FieldType.INT,
#                 required=False,
#             ),
#             FieldPolicy(
#                 key="auth.password",
#                 hint="kein Echo",
#                 type=FieldType.STRING,
#                 secret=True,
#             ),
#         ]
#     )
