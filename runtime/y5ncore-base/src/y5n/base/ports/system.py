from y5n.base.plugins.ports import (
    OnAuthenticate,
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
from y5n.base.sources import OnSourceRead

from .port import Port

# -----------------------
# --- SYSTEM PORTS ------
# -----------------------

AUTHENTICATE = Port(
    "authenticate",
    protocol=OnAuthenticate,
)

SOURCE_READ = Port(
    "source.read",
    protocol=OnSourceRead,
)

SESSION_SAVE = Port(
    "session.save",
    protocol=OnSessionSave,
)

SESSION_ATTACH = Port(
    "session.attach",
    protocol=OnSessionAttach,
)

SESSION_DETACH = Port(
    "session.detach",
    protocol=OnSessionDetach,
)

AUTHORIZE_READ = Port(
    "auth.read",
    protocol=OnAuthorizeRead,
)

AUTHORIZE_WRITE = Port(
    "auth.write",
    protocol=OnAuthorizeWrite,
)

NEW_PERMISSION_SET = Port(
    "permission.new",
    protocol=OnNewPermissionSet,
)

PARSE_PERMISSION_SPEC = Port(
    "permission.parse",
    protocol=OnParsePermissionSpec,
)

PROJECT = Port(
    "projection.project",
    protocol=OnProject,
)

PROJECTION_RESOLVE = Port(
    "projection.resolve",
    protocol=OnProjectionResolve,
)

RESOURCE_LOAD = Port(
    "resource.load",
    protocol=OnResourceLoad,
)

JINJA_RENDER = Port(
    "jinja.render",
    protocol=OnJinjaRender,
)

COMPILE = Port(
    "compile",
    protocol=OnCompile,
)

ERROR_RESOLVE = Port(
    "error.resolve",
    protocol=OnErrorResolve,
)
