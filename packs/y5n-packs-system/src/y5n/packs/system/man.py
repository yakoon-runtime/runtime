from y5n.sdk import context, ports, runtime


async def main():
    req = context.request()
    key = req.arg(0)

    if not key:
        doc = ports.get("document")
        result = await doc.render(state={})
        await runtime.io.write(result)
        return

    src = ports.get("source")
    ctx = context.current()
    lookup = key
    current = ctx.cwd
    if current and current != "/" and not key.startswith("/"):
        lookup = f"{current}/{key}"

    result = await src.read(query=f"system:nodes --by-key {lookup}")
    if result.status != "ok" and lookup != key:
        result = await src.read(query=f"system:nodes --by-key {key}")
    else:
        key = lookup

    if result.status == "ok":
        node_data = result.one()
        node_path = node_data.get("path")

        if node_path and await runtime.supports(node_path=node_path, capability="man"):

            resource = await runtime.resolve(node_path=node_path, capability="man")
            template = resource.read_text()
            jinja = ports.get("jinja")
            html = await jinja(content=template, context={"key": key})
            compile_port = ports.get("compile")
            projection = await compile_port(text=html, context={})
            await runtime.io.write(projection)
            return

    await runtime.io.write(f"No man page for '{key}'")
