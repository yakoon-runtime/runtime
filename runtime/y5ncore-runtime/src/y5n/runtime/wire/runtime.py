from y5n.base.document import Document
from y5n.base.nodes import NodePath, UnknownOptionsError, UsageError
from y5n.base.ports.system import (
    AUTHORIZE_READ,
    AUTHORIZE_WRITE,
    COMPILE,
    DOCUMENT,
    DOCUMENT_RESOLVE,
    ERROR_RESOLVE,
    JINJA_RENDER,
    NEW_PERMISSION_SET,
    PARSE_PERMISSION_SPEC,
    RESOURCE_LOAD,
    SESSION_ATTACH,
    SESSION_DETACH,
    SESSION_SAVE,
    SOURCE_READ,
    VALIDATE,
)
from y5n.base.resources import ResourceRef
from y5n.base.runtime import get_bus
from y5n.runtime.capabilities.audit import AuditLogService
from y5n.runtime.capabilities.permission import (
    PermissionChecker,
    PermissionParser,
    PermissionSet,
)
from y5n.runtime.document.rendering import JinjaRenderEngine
from y5n.runtime.executor import (
    ExecutorKind,
    ExecutorRegistry,
    ProcessExecutor,
    PythonExecutor,
    RuntimeExecutor,
    ScriptExecutor,
)
from y5n.runtime.nodes.tree import Tree
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
from y5n.runtime.wire.adapter.document import DocumentAdapter
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

    # -----------------------
    # --- EXECUTOR SETUP ---
    # -----------------------

    executors = ExecutorRegistry()
    executors.register(ExecutorKind.RUNTIME, RuntimeExecutor())
    executors.register(ExecutorKind.PYTHON, PythonExecutor())
    executors.register(ExecutorKind.SCRIPT, ScriptExecutor())
    executors.register(ExecutorKind.PROCESS, ProcessExecutor())

    # -----------------------
    # --- YAK TREE BUILD ---
    # -----------------------

    tree = Tree(
        root_path=settings.runtime.workspace_path,
        executors=executors,
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
    ) -> Document:

        if isinstance(error, PermissionDenied):
            audit_service.security(session=session, obj="command", action=root.key)  # type: ignore
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
    root = tree.root()

    assert root
    root_ports = root.ports

    root_ports.provide(SOURCE_READ, ds.read)
    root_ports.provide(SESSION_SAVE, session_manager.save)
    root_ports.provide(AUTHORIZE_READ, perm_checker.can_read)
    root_ports.provide(AUTHORIZE_WRITE, perm_checker.can_write)
    root_ports.provide(NEW_PERMISSION_SET, lambda: PermissionSet())
    root_ports.provide(PARSE_PERMISSION_SPEC, perm_parser.parse)
    root_ports.provide(DOCUMENT, projector.project_from_space)
    root_ports.provide(DOCUMENT_RESOLVE, projector.project)
    root_ports.provide(RESOURCE_LOAD, package_reader.get_text)
    root_ports.provide(JINJA_RENDER, jinja_engine.render_str)
    root_ports.provide(COMPILE, compiler.compile)
    root_ports.provide(ERROR_RESOLVE, error_resolve)
    root_ports.provide(VALIDATE, tree.validate)

    # ---------------------------------------
    # --- SDK ADAPTERS (on the Runtime Bus) ---
    # ---------------------------------------

    bus = get_bus()
    bus.resolver.register("system:projection", {"document": ["render"]}, path="/")

    bus.transport.register_adapter(
        "document",
        DocumentAdapter(projector=projector, tree=tree),
    )

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
        await tree.setup()
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
        platform=root,
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
    root_ports.provide(SESSION_ATTACH, host.attach_session)
    root_ports.provide(SESSION_DETACH, host.detach_session)

    return host
