from typing import Literal, TypeAlias

from y5n.base.nodes import Node, NodePath, NodeScope, UnknowOptionsError, UsageError
from y5n.base.plugins.ports import (
    OnAuthorizeRead,
    OnAuthorizeWrite,
    OnCompile,
    OnErrorResolve,
    OnJinjaRender,
    OnProjectionResolve,
    OnResourceLoad,
    OnSessionSave,
)
from y5n.base.projection import Projection
from y5n.base.resources import ResourceRef
from y5n.base.sources import OnSourceRead
from y5n.runtime.capabilities.audit import AuditLogService
from y5n.runtime.capabilities.permission import (
    PermissionChecker,
)
from y5n.runtime.projection.rendering import JinjaRenderEngine
from y5n.runtime.resources import PackageReader
from y5n.runtime.runtime import (
    NodeNotFound,
    PermissionDenied,
    Session,
    SessionService,
)
from y5n.runtime.services import GuidanceService
from y5n.runtime.settings import Settings
from y5n.runtime.sources import DataSourceRegistry
from y5n.runtime.sources.data import (
    NodeSource,
)
from y5n.runtime.wire.compiler import build_compiler
from y5n.runtime.wire.machine import RuntimeHost, build_machine
from y5n.runtime.wire.plugins import PluginLoader
from y5n.runtime.wire.projector import build_projector
from y5n.runtime.wire.stream import build_stream
from y5nstore.event.wire import build_store

CapabilityMode: TypeAlias = Literal["default"]
CapabilitySelection: TypeAlias = dict[str, CapabilityMode | None]


errors = {
    Exception: "error.sam",
    NodeNotFound: "command/not_found.sam",
    UsageError: "command/usage.sam",
    UnknowOptionsError: "command/unknown_options.sam",
    PermissionDenied: "permissions/denied.sam",
}


def build_runtime(
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

    package_reader = PackageReader()
    jinja_engine = JinjaRenderEngine()
    projector = build_projector()
    compiler = build_compiler()

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

    # -----------------
    # --- ROOT NODE ---
    # -----------------

    platform = Node(
        key="platform",
        scope=NodeScope.NODE,
    )

    # -----------------------
    # --- ERROR RESOLVING ---
    # -----------------------

    async def error_resolve(
        *,
        key: NodePath,
        session: Session,
        error: Exception,
    ) -> Projection:

        if isinstance(error, PermissionDenied):
            audit_service.security(session=session, obj="command", action=node.key)
        elif type(error) not in errors:
            audit_service.error(exc=error, session=session)

        parts = errors.get(type(error), "error.sam")
        resource = ResourceRef(
            package="y5n.runtime",
            path=f"templates/{session.lang}/{parts}",
        )

        return await projector.project(
            resource=resource,
            state=vars(error),
        )

    # ----------------
    # --- BINDINGS ---
    # ----------------

    platform.ports.provide(OnSourceRead, ds.read)
    platform.ports.provide(OnSessionSave, session_manager.save)
    platform.ports.provide(OnAuthorizeRead, perm_checker.can_read)
    platform.ports.provide(OnAuthorizeWrite, perm_checker.can_write)
    platform.ports.provide(OnProjectionResolve, projector.project)
    platform.ports.provide(OnResourceLoad, package_reader.get_text)
    platform.ports.provide(OnJinjaRender, jinja_engine.render_str)
    platform.ports.provide(OnCompile, compiler.compile)
    platform.ports.provide(OnErrorResolve, error_resolve)

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
        platform=platform,
        on_suggest=guidance_service.suggest,
        on_session=session_manager.get_or_create,
        on_projection_send=output.send_projection,
        on_has_permission=perm_checker.can_execute,
        on_audit_warning=audit_service.warning,
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
