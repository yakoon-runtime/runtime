import os

from y5n.api.dsl import out_text, receive, run_task
from y5n.api.dsl.patterns import Form

SCRIPT = os.path.join(
    os.path.dirname(__file__),
    "helper",
    "generate_pdf.py",
)


async def run(_):

    form = Form()

    yield form.ask(key="name", title="Name")
    yield form.ask(key="greeting", title="Greeting")

    name = form.data.get("name", "World")
    greeting = form.data.get("greeting", "Hello")

    yield out_text(f"Generating PDF for {name}...")

    task = run_task(
        "python3",
        args=[SCRIPT, "--name", name, "--greeting", greeting],
    )

    yield task

    result = yield receive(task.channel)
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
