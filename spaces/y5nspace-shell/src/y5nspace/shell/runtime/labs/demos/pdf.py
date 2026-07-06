import os
from uuid import uuid4

from y5n.api.dsl import out_text, receive, start_task
from y5n.api.dsl.patterns import Form
from y5n.api.invocations import Param
from y5n.base.flow.channel import Scope

SCRIPT = os.path.join(
    os.path.dirname(__file__),
    "helper",
    "generate_pdf.py",
)


async def run(_):

    form = Form(
        title="PDF",
        fields=[
            Param(key="name", title="Name"),
            Param(key="greeting", title="Greeting"),
        ],
    )

    async for outcome in form.run():
        yield outcome

    name = form.values.get("name", "World")
    greeting = form.values.get("greeting", "Hello")

    yield out_text(f"Generating PDF for {name}...")

    ch = uuid4().hex
    yield start_task("python3", channel=ch, args=[SCRIPT, "--name", name, "--greeting", greeting])

    result = yield receive(ch, scope=Scope.SESSION)
    payload = result.payload or {}

    lines = [
        f"\u2192 returncode={payload.get('returncode')}",
    ]

    stdout = payload.get("stdout", "").strip()
    if stdout:
        lines.append(f"\u2192 stdout={stdout}")

    stderr = payload.get("stderr", "").strip()
    if stderr:
        lines.append(f"\u2192 stderr={stderr}")

    yield out_text("\n".join(lines))
