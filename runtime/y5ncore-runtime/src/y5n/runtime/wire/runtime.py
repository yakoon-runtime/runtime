from y5n.base.nodes import Node, NodePath, UnknownOptionsError, UsageError
from y5n.base.plugins.ports import (
    OnAuthorizeRead,
    OnAuthorizeWrite,
    OnCompile,
    OnErrorResolve,
    OnJinjaRender,
    OnNewPermissionSet,
    OnParsePermissionSpec,
    OnProject,
    OnProjectionResolve,
    OnResourceLoad,
    OnSessionAttach,
    OnSessionDetach,
    OnSessionSave,
)
from y5n.base.projection import Projection
from y5n.base.resources import ResourceRef
from y5n.base.sources import OnSourceRead
from y5n.runtime.capabilities.audit import AuditLogService
from y5n.runtime.capabilities.permission import (
    PermissionChecker,
    PermissionParser,
    PermissionSet,
)
from y5n.runtime.nodes.tree import Tree
from y5n.runtime.projection.rendering import JinjaRenderEngine
from y5n.runtime.resources import PackageReader
from y5n.runtime.runtime import (
    NodeNotExecutable,
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
    RuntimeSource,
    SessionSource,
)
from y5n.runtime.wire.compiler import build_compiler
from y5n.runtime.wire.machine import RuntimeHost, build_machine
from y5n.runtime.wire.projector import build_projector
from y5n.runtime.wire.stream import build_stream
from y5nstore.event.wire import build_store

errors = {
    Exception: "error.yak",
    NodeNotFound: "command/not_found.yak",
    NodeNotExecutable: "command/not_executable.yak",
    UsageError: "command/usage.yak",
    UnknownOptionsError: "command/unknown_options.yak",
    PermissionDenied: "permissions/denied.yak",
}


def build_runtime(
    *,
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
    perm_parser = PermissionParser()

    # --------------------
    # --- DATASOURCING ---
    # --------------------

    ds = DataSourceRegistry()

    # -----------------
    # --- ROOT NODE ---
    # -----------------

    platform = Node(
        key="/",
    )

    # -----------------------
    # --- YAK TREE BUILD ---
    # -----------------------

    tree = Tree(
        root_ports=platform.ports,
        root_path=settings.runtime.root_path,
    )

    tree.build()

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

        parts = errors.get(type(error), "error.yak")
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
    platform.ports.provide(OnNewPermissionSet, lambda: PermissionSet())
    platform.ports.provide(OnParsePermissionSpec, perm_parser.parse)
    platform.ports.provide(OnProject, projector.project_from_space)
    platform.ports.provide(OnProjectionResolve, projector.project)
    platform.ports.provide(OnResourceLoad, package_reader.get_text)
    platform.ports.provide(OnJinjaRender, jinja_engine.render_str)
    platform.ports.provide(OnCompile, compiler.compile)
    platform.ports.provide(OnErrorResolve, error_resolve)

    # --------------------
    # --- DATASOURCING ---
    # --------------------

    ds.bind("system:nodes", NodeSource(tree))
    ds.bind("system:runtimes", RuntimeSource(settings.runtime.known))
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

    host = build_machine(
        platform=platform,
        on_suggest=guidance_service.suggest,
        on_session=session_manager.get_or_create,
        on_projection_send=output.send_projection,
        on_has_permission=perm_checker.can_execute,
        on_audit_warning=audit_service.warning,
        on_initialize=initialize,
        known_runtimes=settings.runtime.known,
        settings=settings,
        on_get_node=tree.resolve,
    )

    ds.bind("system:sessions", SessionSource(host))
    platform.ports.provide(OnSessionAttach, host.attach_session)
    platform.ports.provide(OnSessionDetach, host.detach_session)

    return host
