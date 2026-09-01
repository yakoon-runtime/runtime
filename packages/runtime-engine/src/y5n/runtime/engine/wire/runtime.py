from pathlib import Path
from typing import cast

from y5n.runtime.api.clients import SessionNotFound
from y5n.runtime.api.naming import Key
from y5n.runtime.api.runtime import get_bus
from y5n.runtime.engine.executor import (
    ExecutorKind,
    ExecutorRegistry,
    RuntimeExecutor,
)
from y5n.runtime.engine.installation import (
    RUNTIME_STORE,
    build_store_registry,
    load_installation,
)
from y5n.runtime.engine.nodes.tree import Tree
from y5n.runtime.engine.runtime import Session, SessionService
from y5n.runtime.engine.runtime.bus import BusOutput
from y5n.runtime.engine.services import GuidanceService, RuntimeLogService
from y5n.runtime.engine.services.activity import ActivityService
from y5n.runtime.engine.services.permissions import PermissionChecker
from y5n.runtime.engine.settings import Settings
from y5n.runtime.engine.sources import DataSourceRegistry
from y5n.runtime.engine.sources.data import (
    NodeSource,
    RuntimeSource,
    SessionSource,
)
from y5n.runtime.engine.wire.adapter import (
    CallableAdapter,
    DocumentAdapter,
    PermissionAdapter,
    ResourceAdapter,
    RuntimeAdapter,
    SessionAdapter,
    SourceReadAdapter,
    StoreAdapter,
)
from y5n.runtime.engine.wire.document import build_document_stack
from y5n.runtime.engine.wire.machine import RuntimeManager, build_machine
from y5n.runtime.engine.wire.stream import build_stream


def build_runtime(
    *,
    settings: Settings,
) -> RuntimeManager:

    # -----------------
    # --- STORAGING ---
    # -----------------

    installation = load_installation(
        Path(settings.runtime.installation_path)
        if settings.runtime.installation_path
        else Path(settings.runtime.workspace_path).parent / "deployment.yml"
    )

    if installation is None:
        raise RuntimeError("No installation found. Run `yak install` to create one.")

    registry = build_store_registry(installation)
    runtime_store = registry.get(RUNTIME_STORE)
    if runtime_store is None:
        raise RuntimeError(
            f"The installation binds no '{RUNTIME_STORE}' store. "
            "The runtime requires it for its session and activity infrastructure."
        )

    # ----------------
    # --- SERVICES ---
    # ----------------

    guidance_service = GuidanceService()
    audit_service = RuntimeLogService(settings.logging)

    activity_service = ActivityService(
        on_record=runtime_store.objects.record,
        on_ensure_indexes=runtime_store.objects.ensure_indexes,
    )

    session_manager = SessionService(
        on_replace=runtime_store.objects.replace,
        on_get=runtime_store.objects.get,
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
        await runtime_store.initialize()
        await activity_service.ensure_index()
        await tree.setup()

    # ------------------------
    # --- MACHINE HANDLING ---
    # ------------------------

    async def resume_session(key: Key) -> Session:
        """Resume an existing session by key (explicit resume contract).

        The session must already exist — live in this process or persisted
        by an earlier one. An unknown key fails instead of creating a
        session under it. A persisted document crosses the process
        boundary in SessionService.get: authentication and elevation are
        reset there and the reset is persisted immediately.
        """
        session = await session_manager.get(key)
        if session is None:
            raise SessionNotFound(f"Session {key} not found")
        psession = cast(Session, session)
        psession.bind_io(BusOutput(psession._bus))
        if not psession.get_data("fs:root"):
            psession.set_data("fs:root", settings.runtime.workspace_path)
            psession.set_cwd("/")
        return psession

    manager = build_machine(
        platform=root,
        on_suggest=guidance_service.suggest,
        on_session=session_manager.get_or_create,
        on_resume_session=resume_session,
        on_projection_send=output.send_document,
        on_has_permission=perm_checker.check,
        on_audit_warning=audit_service.warning,
        on_activity=activity_service.record,
        on_initialize=initialize,
        known_runtimes=settings.runtime.known,
        settings=settings,
        on_get_node=tree.resolve,
    )

    ds.bind("system:sessions", SessionSource(manager))

    # ---------------
    # --- SDK BUS ---
    # ---------------

    bus = get_bus()

    # --------------------
    # --- SDK ADAPTERS ---
    # --------------------

    bus.resolver.register("system:document", {"document": ["render"]}, path="/")
    bus.transport.register_adapter(
        "system:document",
        DocumentAdapter(projector=projector, tree=tree),
    )

    bus.resolver.register("system:validate", {"validate": ["__call__"]}, path="/")
    bus.transport.register_adapter(
        "system:validate",
        CallableAdapter(tree.validate),
    )

    bus.resolver.register("system:source", {"source": ["read"]}, path="/")
    bus.transport.register_adapter(
        "system:source",
        SourceReadAdapter(ds),
    )

    bus.resolver.register("system:jinja", {"jinja": ["__call__"]}, path="/")
    bus.transport.register_adapter(
        "system:jinja",
        CallableAdapter(doc.jinja.render_str),
    )

    bus.resolver.register("system:compile", {"compile": ["__call__"]}, path="/")
    bus.transport.register_adapter(
        "system:compile",
        CallableAdapter(doc.compiler.compile),
    )

    bus.resolver.register(
        "system:session",
        {
            "session": [
                "list",
                "attach",
                "detach",
                "update",
                "logout",
                "current",
                "set_permissions",
            ]
        },
        path="/",
    )
    bus.transport.register_adapter(
        "system:session",
        SessionAdapter(manager, on_save=session_manager.save),
    )

    bus.resolver.register(
        "system:runtime", {"runtime": ["flows", "background"]}, path="/"
    )
    bus.transport.register_adapter(
        "system:runtime",
        RuntimeAdapter(manager),
    )

    bus.resolver.register(
        "system:store",
        {
            "store": [
                "get",
                "get_many",
                "append",
                "replace",
                "record",
                "delete",
                "scan",
                "history",
                "ensure_indexes",
                "query_index",
                "next_id",
            ]
        },
        path="/",
    )
    bus.transport.register_adapter(
        "system:store",
        StoreAdapter(stores=registry),
    )

    bus.resolver.register(
        "system:permissions",
        {"permissions": ["check"]},
        path="/",
    )
    bus.transport.register_adapter(
        "system:permissions",
        PermissionAdapter(manager, tree, perm_checker),
    )

    bus.resolver.register(
        "system:runtime.resource",
        {"runtime.resource": ["resolve", "supports"]},
        path="/",
    )
    bus.transport.register_adapter(
        "system:runtime.resource",
        ResourceAdapter(tree),
    )

    return manager
