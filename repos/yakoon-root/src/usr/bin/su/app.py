from __future__ import annotations

from y5n.api.dsl import out
from y5n.api.dsl.patterns import Form
from y5n.api.invocations import Param
from y5n.api.nodes import NodeSpace
from y5n.api.ports import AUTHENTICATE


async def run(space: NodeSpace):

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

    on_auth = space.ports.get(AUTHENTICATE)
    result = await on_auth(
        space=space,
        username=username,
        secret=secret,
    )

    state = {"user": username, "reason": None}
    if result.ok and result.user:
        state["user"] = result.user.get("username", username)
    else:
        state["reason"] = result.reason

    projection = await space.ports.get(DOCUMENT)(
        space=space,
        state=state,
    )
    yield out(projection)
