from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.dsl.patterns import Form
from y5n.api.naming import Key
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnAuthenticate, OnSessionSave

from ..ports import OnProject
from ..services import Namespaces, PermissionResolver

# ----------------------------------
# RUN
# ----------------------------------


async def run(space: NodeSpace):

    namespaces = space.ports.get(Namespaces)
    form = Form()
    request = space.request

    # ----------------------------------
    # CREDENTIALS (Batch oder Form)
    # ----------------------------------

    username = request.arg(0) or request.option("user")
    secret = request.option("password")

    if not username:
        yield form.ask("username", "Benutzername:")
        username = form.data.get("username", "")

    if not secret:
        yield form.ask("password", "Passwort:")
        secret = form.data.get("password", "")

    # ----------------------------------
    # AUTHENTICATE
    # ----------------------------------

    on_authenticate = space.ports.get(OnAuthenticate)
    result = await on_authenticate(
        namespace=namespaces.user_namespace(),
        username=username,
        secret=secret,
    )

    # ----------------------------------
    # RESULT
    # ----------------------------------

    on_project = space.ports.get(OnProject)

    if result.ok and result.user:

        user = result.user
        user_key: Key = user["key"]

        space.session.set_identity(user_key)

        resolver = space.ports.get(PermissionResolver)
        permissions = await resolver.resolve_user_permissions(
            grant_namespace=namespaces.permgrant_namespace(),
            membership_namespace=namespaces.membership_namespace(),
            user_key=user_key,
        )
        space.session.set_permissions(permissions)

        on_save_session = space.ports.get(OnSessionSave)
        await on_save_session(session=space.session)

        projection = await on_project(
            name="su/success",
            lang=request.lang,
            state={"user": user["username"]},
        )

    else:

        projection = await on_project(
            name="su/error",
            lang=request.lang,
            state={"user": username, "reason": result.reason},
        )

    yield out(projection)



