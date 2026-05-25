from typing import Literal, TypeAlias

from yakoon.base.nodes import Node, NodeScope
from yakoon.base.nodes.errors import UnknowOptionsError, UsageError
from yakoon.base.plugins.ports import (
    OnAuthorizeRead,
    OnAuthorizeWrite,
    OnCompile,
    OnErrorResolve,
    OnJinjaRender,
    OnProjectionResolve,
    OnResourceLoad,
    OnSessionSave,
)
from yakoon.base.projection import Projection
from yakoon.base.resources import ResourceRef
from yakoon.base.sources import OnSourceRead
from yakoon.platform.capabilities.audit import AuditLogService
from yakoon.platform.capabilities.permission import (
    PermissionChecker,
)
from yakoon.platform.projection.rendering.engine import JinjaRenderEngine
from yakoon.platform.resources import PackageReader
from yakoon.platform.runtime.error import NodeNotFound, PermissionDenied
from yakoon.platform.runtime.sessions import SessionService
from yakoon.platform.runtime.sessions.session import Session
from yakoon.platform.services import GuidanceService
from yakoon.platform.settings import Settings
from yakoon.platform.sources import DataSourceRegistry
from yakoon.platform.sources.data import (
    NodeSource,
)
from yakoon.platform.wire.compiler import build_compiler
from yakoon.platform.wire.machine import RuntimeHost, build_machine
from yakoon.platform.wire.plugins import PluginLoader
from yakoon.platform.wire.projector import build_projector
from yakoon.platform.wire.stream import build_stream
from yakoon.storage.eventstore.wire import build_store

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
        node: Node,
        session: Session,
        error: Exception,
    ) -> Projection:

        if isinstance(error, PermissionDenied):
            audit_service.security(session=session, obj="command", action=node.key)
        elif type(error) not in errors:
            audit_service.error(exc=error, session=session)

        parts = errors.get(type(error), "error.sam")
        resource = ResourceRef(
            package="yakoon.platform",
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
