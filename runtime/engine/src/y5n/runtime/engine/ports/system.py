from y5n.runtime.engine.ports.protocols import (
    OnAuthenticate,
    OnAuthorizeRead,
    OnAuthorizeWrite,
    OnCompile,
    OnDocumentResolve,
    OnErrorResolve,
    OnJinjaRender,
    OnNewPermissionSet,
    OnParsePermissionSpec,
    OnProject,
    OnResourceLoad,
    OnSessionAttach,
    OnSessionDetach,
    OnSessionSave,
    OnSourceRead,
    OnValidate,
)

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

DOCUMENT = Port(
    "document.project",
    protocol=OnProject,
)

DOCUMENT_RESOLVE = Port(
    "document.resolve",
    protocol=OnDocumentResolve,
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

VALIDATE = Port(
    "validate",
    protocol=OnValidate,
)
