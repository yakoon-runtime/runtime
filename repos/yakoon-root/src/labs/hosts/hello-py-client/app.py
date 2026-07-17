"""Consumes a port service from the runtime."""

from y5n.sdk import context, ports


async def main():
    hello = ports.get("hello")
    print(await hello.greet())
    print(await hello.greet(name="Yakoon"))

    ctx = context.current()
    print(f"path:     {ctx.node.get('path', '?')}")
    print(f"cwd:      {ctx.cwd}")
    print(f"user:     {ctx.user.get('name', ctx.user.get('id', '?'))}")

    ses = context.session()
    print(f"key:      {ses.key}")
    print(f"locale:   {ses.locale}")
    print(f"user_id:  {ses.user_id}")
    print(f"interaction: {ses.interaction}")

    req = context.request()
    print(f"args:     {req.args()}")
    if req.has_option("greet"):
        print(f"--greet value: {req.option('greet')}")
