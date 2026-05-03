from typing import Literal, TypeAlias

from yakoon.base.application import Application
from yakoon.base.plugins import ModulePorts
from yakoon.base.plugins.ports import (
    OnAuthorize,
    OnProject,
    OnSaveSession,
)
from yakoon.base.runtime import Container
from yakoon.base.sources import OnDataSource
from yakoon.platform.capabilities.audit.service import DefaultAuditLogService
from yakoon.platform.capabilities.identity.services.permission import (
    PermissionService,
)
from yakoon.platform.machine.host import RuntimeHost
from yakoon.platform.machine.wire import build_machine
from yakoon.platform.plugins import PluginLoader
from yakoon.platform.projection import (
    build_projector,
    build_stream,
)
from yakoon.platform.runtime import SessionManager
from yakoon.platform.sources.data import (
    AppSource,
    CommandSource,
)
from yakoon.platform.sources.registry import DataSourceRegistry
from yakoon.storage.eventstore.wire import build_memory_store

CapabilityMode: TypeAlias = Literal["default"]
CapabilitySelection: TypeAlias = dict[str, CapabilityMode | None]


def compose_runtime(
    *,
    plugins: list[str] | None = None,
    capabilities: CapabilitySelection | None = None,
) -> RuntimeHost:

    ports = Container()

    plugins = plugins or []
    capabilities = capabilities or {}

    # ----------------------
    # --- BUILDING STORE ---
    # ----------------------

    store = build_memory_store()

    # ----------------
    # --- SERVICES ---
    # ----------------

    session_manager = SessionManager(
        on_save=store.objects.replace,
        on_load=store.objects.get_one,
    )

    permission_service = PermissionService()
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
    ds.bind("system:commands", CommandSource(applications))

    # ----------------
    # --- BINDINGS ---
    # ----------------

    def bind_ports() -> ModulePorts:

        fork = ports.fork()

        fork.bind(OnDataSource, ds.read)
        fork.bind(OnProject, projector.project)
        fork.bind(OnSaveSession, session_manager.save)
        fork.bind(OnAuthorize, permission_service.can_read)

        return ModulePorts(
            on_publish=ports.bind,
            on_provide=fork.bind,
            on_get_port=fork.get,
        )

    for app in applications:
        app.bind_ports(bind_ports())

    # _compose_permission_roles(bootstrap)
    # _compose_policies(bootstrap)

    # --- STREAMING ---

    output = build_stream()

    # --- MACHINE HANDLING ---

    return build_machine(
        applications=applications,
        on_session=session_manager.get_or_create,
        on_projection=output.send_projection,
        on_authorize=permission_service.can_execute,
        on_bootstrap_permissions=permission_service.set_bootstrap_permissions,
        on_audit_log=audit_service.audit,
        on_audit_error=audit_service.error,
        on_audit_security=audit_service.security,
        on_audit_warning=audit_service.warning,
    )


# def _compose_permission_roles():
#     permissions = "PermissionService"
#     permissions.register_role(
#         "admin",
#         [
#             "app-app:su|rx",
#             "shell-app:use|rx",
#             "office.mailing:sendmail|rx",
#         ],
#     )
#     permissions.register_role(
#         "user",
#         [
#             "shell-app:use|rx",
#         ],
#     )


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


# async def initialize_storage(container: Container) -> None:
#     index = container.get(strategie.IndexRegistry)

#     from yakoon.platform.capabilities.identity.services.account_service import (
#         IDX_ACCOUNT_USERNAME_SPEC,
#     )

#     await index.ensure(
#         namespace=Namespace("system", "account", "develop"),
#         specs=[
#             IDX_ACCOUNT_USERNAME_SPEC,
#         ],
#     )
