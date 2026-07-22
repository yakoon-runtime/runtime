"""Consumes a port service from the runtime."""

from y5n.sdk import context, ports, runtime


async def main():
    hello = ports.get("hello")
    await runtime.io.write(await hello.greet())
    await runtime.io.write(await hello.greet(name="Yakoon"))

    # -- context --
    ctx = context.current()
    await runtime.io.write(f"path:     {ctx.node.get('path', '?')}")
    await runtime.io.write(f"cwd:      {ctx.cwd}")
    await runtime.io.write(f"user:     {ctx.user.get('name', ctx.user.get('id', '?'))}")

    # -- session --
    ses = context.session()
    await runtime.io.write(f"key:      {ses.key}")
    await runtime.io.write(f"locale:   {ses.locale}")
    await runtime.io.write(f"user_id:  {ses.user_id}")

    # -- request --
    req = context.request()
    await runtime.io.write(f"args:     {req.args()}")
    if req.has_option("greet"):
        await runtime.io.write(f"--greet value: {req.option('greet')}")
