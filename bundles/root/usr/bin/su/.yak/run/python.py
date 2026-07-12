from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.dsl.patterns import Form
from y5n.api.invocations import Param
from y5n.api.naming import Key
from y5n.api.nodes import NodeSpace
from y5n.api.ports import AUTHENTICATE, OnSessionSave, PROJECT


async def run(space: NodeSpace):

    namespaces = space.ports.get("namespaces")

    request = space.request

    username = request.arg(0) or request.option("user")
    secret = request.option("password")

    if not username or not secret:
        initial = {}
        if username:
            initial["username"] = username
        if secret:
            initial["password"] = secret

        form = Form(
            title="Login",
            fields=[
                Param(key="username", title="Benutzername"),
                Param(key="password", title="Passwort"),
            ],
            initial=initial,
            focus="password" if username else None,
        )

        async for step in form.run():
            yield step

        username = form.data.get("username") or username
        secret = form.data.get("password") or secret

    on_authenticate = space.ports.get(AUTHENTICATE)
    result = await on_authenticate(
        namespace=namespaces.user_namespace(),
        username=username,
        secret=secret,
    )

    state = {"user": username, "reason": None}
    if result.ok and result.user:
        user = result.user
        user_key: Key = user["key"]
        user_name = user["username"]

        space.session.set_identity(user_key, user_name)
        space.session.set_current_path("/")

        resolver = space.ports.get("permissions.resolve")
        permissions = await resolver.resolve_user_permissions(
            grant_namespace=namespaces.permgrant_namespace(),
            join_namespace=namespaces.join_namespace(),
            user_key=user_key,
        )
        space.session.set_permissions(permissions)

        on_save_session = space.ports.get(OnSessionSave)
        await on_save_session(session=space.session)

        state["user"] = user_name
    else:
        state["reason"] = result.reason

    projection = await space.ports.get(PROJECT)(
        space=space,
        state=state,
    )
    yield out(projection)
