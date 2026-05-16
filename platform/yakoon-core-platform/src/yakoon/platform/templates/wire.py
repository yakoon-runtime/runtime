from __future__ import annotations

from typing import Protocol

from yakoon.base.commands.errors import UnknowOptionsError, UsageError
from yakoon.base.resources.resource import ResourceRef
from yakoon.platform.runtime.error import (
    NodeNotFound,
    PermissionDenied,
    UnhandledError,
)

PACKAGE = "yakoon.platform"


def register_templates(on_register: OnRegister):

    _register_for(on_register, "de")
    _register_for(on_register, "en")


# ----------------------------------
# INTERNALS
# ----------------------------------


def _register_for(on_register: OnRegister, lang="de"):

    # ----------------------------------
    # ALL ERRORS
    # ----------------------------------

    on_register(
        key=str(type(UnhandledError())),
        scope="system",
        resource=ResourceRef(
            package=PACKAGE,
            path=f"templates/errors/{lang}/error",
        ),
        lang=lang,
    )

    # ----------------------------------
    # COMMAND ERRORS
    # ----------------------------------

    on_register(
        key=str(type(NodeNotFound())),
        scope="system",
        resource=ResourceRef(
            package=PACKAGE,
            path=f"templates/errors/{lang}/command/not_found",
        ),
        lang=lang,
    )

    on_register(
        key=str(type(UsageError())),
        scope="system",
        resource=ResourceRef(
            package=PACKAGE,
            path=f"templates/errors/{lang}/command/usage",
        ),
        lang=lang,
    )

    on_register(
        key=str(type(UnknowOptionsError())),
        scope="system",
        resource=ResourceRef(
            package=PACKAGE,
            path=f"templates/errors/{lang}/command/unknown_options",
        ),
        lang=lang,
    )

    # ----------------------------------
    # PERMISSION ERRORS
    # ----------------------------------

    on_register(
        key=str(type(PermissionDenied())),
        scope="system",
        resource=ResourceRef(
            package=PACKAGE,
            path=f"templates/errors/{lang}/permission/denied",
        ),
        lang=lang,
    )


# ----------------------------------
# PORTS
# ----------------------------------


class OnRegister(Protocol):
    def __call__(
        self,
        scope: str,
        key: str,
        resource: ResourceRef,
        lang: str,
        renderer: str | None = None,
        theme: str | None = None,
        priority: int = 0,
    ) -> None: ...
