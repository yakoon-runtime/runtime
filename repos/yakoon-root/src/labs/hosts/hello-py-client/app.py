"""Consumes a port service from the runtime."""

from y5n.sdk import context, ports, runtime


async def main():
    hello = ports.get("hello")
    await runtime.write(await hello.greet())
    await runtime.write(await hello.greet(name="Yakoon"))

    # -- context --
    ctx = context.current()
    await runtime.write(f"path:     {ctx.node.get('path', '?')}")
    await runtime.write(f"cwd:      {ctx.cwd}")
    await runtime.write(f"user:     {ctx.user.get('name', ctx.user.get('id', '?'))}")

    # -- session --
    ses = context.session()
    await runtime.write(f"key:      {ses.key}")
    await runtime.write(f"locale:   {ses.locale}")
    await runtime.write(f"user_id:  {ses.user_id}")
    await runtime.write(f"interaction: {ses.interaction}")

    # -- request --
    req = context.request()
    await runtime.write(f"args:     {req.args()}")
    if req.has_option("greet"):
        await runtime.write(f"--greet value: {req.option('greet')}")
