from y5n.runtime.api.runtime import get_bus
from y5n.runtime.engine.capabilities.audit import AuditLogService
from y5n.runtime.engine.capabilities.permission import PermissionChecker
from y5n.runtime.engine.executor import (
    ExecutorKind,
    ExecutorRegistry,
    RuntimeExecutor,
)
from y5n.runtime.engine.nodes.tree import Tree
from y5n.runtime.engine.runtime import SessionService
from y5n.runtime.engine.services import GuidanceService
from y5n.runtime.engine.settings import Settings
from y5n.runtime.engine.sources import DataSourceRegistry
from y5n.runtime.engine.sources.data import (
    NodeSource,
    RuntimeSource,
    SessionSource,
)
from y5n.runtime.engine.wire.adapter.callable import CallableAdapter
from y5n.runtime.engine.wire.adapter.document import DocumentAdapter
from y5n.runtime.engine.wire.adapter.resource import ResourceAdapter
from y5n.runtime.engine.wire.adapter.runtime import RuntimeAdapter
from y5n.runtime.engine.wire.adapter.session import SessionAdapter
from y5n.runtime.engine.wire.adapter.source import SourceReadAdapter
from y5n.runtime.engine.wire.document import build_document_stack
from y5n.runtime.engine.wire.machine import RuntimeManager, build_machine
from y5n.runtime.engine.wire.stream import build_stream
from y5n.runtime.store.event.wire import build_store


def build_runtime(
    *,
    settings: Settings,
) -> RuntimeManager:

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

    # --------------------
    # --- DATASOURCING ---
    # --------------------

    ds = DataSourceRegistry()

    # -----------------------
    # --- EXECUTOR SETUP ---
    # -----------------------

    executors = ExecutorRegistry()
    executors.register(ExecutorKind.RUNTIME, RuntimeExecutor())

    # -----------------------
    # --- YAK TREE BUILD ---
    # -----------------------

    tree = Tree(
        root_path=settings.runtime.workspace_path,
        executors=executors,
    )

    tree.build()

    # ----------------
    # --- DOCUMENT ---
    # ----------------

    doc = build_document_stack(tree=tree)
    projector = doc.projector

    # --------------------
    # --- DATASOURCING ---
    # --------------------

    ds.bind("system:nodes", NodeSource(tree))
    ds.bind("system:runtimes", RuntimeSource(settings.runtime.known))
    # ds.bind("system:discovery", DiscoverySource(ds.read, perm_checker.can_read))

    root = tree.root()
    assert root

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

    # ------------------------
    # --- MACHINE HANDLING ---
    # ------------------------

    manager = build_machine(
        platform=root,
        on_suggest=guidance_service.suggest,
        on_session=session_manager.get_or_create,
        on_projection_send=output.send_document,
        on_has_permission=perm_checker.can_execute,
        on_audit_warning=audit_service.warning,
        on_initialize=initialize,
        known_runtimes=settings.runtime.known,
        settings=settings,
        on_get_node=tree.resolve,
    )

    ds.bind("system:sessions", SessionSource(manager))

    # ---------------------------------------
    # --- SDK ADAPTERS (on the Runtime Bus) ---
    # ---------------------------------------

    bus = get_bus()

    bus.resolver.register("system:projection", {"document": ["render"]}, path="/")
    bus.transport.register_adapter(
        "document",
        DocumentAdapter(projector=projector, tree=tree),
    )

    bus.resolver.register("system:projection", {"validate": ["__call__"]}, path="/")
    bus.transport.register_adapter(
        "validate",
        CallableAdapter(tree.validate),
    )

    bus.resolver.register("system:projection", {"source": ["read"]}, path="/")
    bus.transport.register_adapter(
        "source",
        SourceReadAdapter(ds),
    )

    bus.resolver.register("system:projection", {"jinja": ["__call__"]}, path="/")
    bus.transport.register_adapter(
        "jinja",
        CallableAdapter(doc.jinja.render_str),
    )

    bus.resolver.register("system:projection", {"compile": ["__call__"]}, path="/")
    bus.transport.register_adapter(
        "compile",
        CallableAdapter(doc.compiler.compile),
    )

    bus.resolver.register(
        "system:projection",
        {"session": ["attach", "detach", "update", "logout", "current"]},
        path="/",
    )
    bus.transport.register_adapter(
        "session",
        SessionAdapter(manager, on_save=session_manager.save),
    )

    bus.resolver.register(
        "system:projection", {"runtime": ["flows", "background"]}, path="/"
    )
    bus.transport.register_adapter(
        "runtime",
        RuntimeAdapter(manager),
    )

    bus.resolver.register(
        "system:projection",
        {"runtime.resource": ["resolve", "supports"]},
        path="/",
    )
    bus.transport.register_adapter(
        "runtime.resource",
        ResourceAdapter(tree),
    )

    return manager
