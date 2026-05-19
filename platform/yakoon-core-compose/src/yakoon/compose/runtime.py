from typing import Literal, TypeAlias

from yakoon.base.nodes import Node, NodeScope
from yakoon.base.plugins.ports import (
    OnAuthorizeRead,
    OnAuthorizeWrite,
    OnProject,
    OnSaveSession,
)
from yakoon.base.sources import OnDataSource
from yakoon.platform.capabilities.audit import AuditLogService
from yakoon.platform.capabilities.permission import (
    PermissionChecker,
)
from yakoon.platform.machine.host import RuntimeHost
from yakoon.platform.machine.wire import build_machine
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
    NodeSource,
)
from yakoon.platform.sources.registry import DataSourceRegistry
from yakoon.platform.templates.wire import register_templates
from yakoon.storage.eventstore.wire import build_store

from .resource import get_resource

CapabilityMode: TypeAlias = Literal["default"]
CapabilitySelection: TypeAlias = dict[str, CapabilityMode | None]


def compose_runtime(
    *,
    plugins: list[str] | None = None,
    capabilities: CapabilitySelection | None = None,
    settings: Settings,
) -> RuntimeHost:

    # -----------------
    # --- STORAGING ---
    # -----------------

    store = build_store(settings.storage)

    # ----------------
    # --- SERVICES ---
    # ----------------

    guidance_service = GuidanceService()
    audit_service = AuditLogService(settings.logging)
    session_manager = SessionService(
        on_replace=store.objects.replace,
        on_get=store.objects.get,
    )

    # -------------------
    # --- PERMISSIONS ---
    # -------------------

    perm_checker = PermissionChecker()

    # -----------------
    # --- PROJECTOR ---
    # -----------------

    projections = ProjectionRegistry()
    register_templates(projections.register)

    projector = build_projector()

    # ----------------
    # --- PLUGINS ---
    # ----------------

    nodes: list[Node] = []
    for module in PluginLoader(plugins or [], capabilities or {}).load():
        if module.export.node:
            nodes.append(module.export.node)

    # --------------------
    # --- DATASOURCING ---
    # --------------------

    ds = DataSourceRegistry()

    # ----------------
    # --- BINDINGS ---
    # ----------------

    platform = Node(
        key="platform",
        scope=NodeScope.NODE,
        on_resource=get_resource,
    )

    platform.ports.provide(OnDataSource, ds.read)
    platform.ports.provide(OnProject, projector.project)
    platform.ports.provide(OnSaveSession, session_manager.save)
    platform.ports.provide(OnAuthorizeRead, perm_checker.can_read)
    platform.ports.provide(OnAuthorizeWrite, perm_checker.can_write)

    # -----------------
    # --- ATTACHING ---
    # -----------------

    for node in nodes:
        platform.mount(node)

    # --------------------
    # --- DATASOURCING ---
    # --------------------

    ds.bind("system:nodes", NodeSource(platform))
    # ds.bind("system:discovery", DiscoverySource(ds.read, perm_checker.can_read))

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
        root=platform,
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
