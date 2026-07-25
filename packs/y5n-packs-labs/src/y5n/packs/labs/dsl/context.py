"""Demonstrates context, session, and request access."""

from y5n.sdk import context, io


async def main():
    ctx = context.current()
    await io.write(f"path:     {ctx.node.get('path', '?')}")
    await io.write(f"cwd:      {ctx.cwd}")
    await io.write(f"user:     {ctx.user.get('name', ctx.user.get('id', '?'))}")

    ses = context.session()
    await io.write(f"key:      {ses.key}")
    await io.write(f"locale:   {ses.locale}")
    await io.write(f"user_id:  {ses.user_id}")

    req = context.request()
    await io.write(f"args:     {req.args()}")
    if req.has_option("greet"):
        await io.write(f"--greet value: {req.option('greet')}")
