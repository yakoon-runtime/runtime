from pathlib import Path

from y5n.sdk import context, ports


async def main():
    req = context.request()
    key = req.arg(0)

    if not key:
        doc = ports.get("document")
        result = await doc.render(state={})
        print(result)
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
        resources = node_data.get("resources", {})
        man_res = resources.get("man", {})
        template_path = man_res.get("default")

        if template_path:
            import json

            template = Path(template_path).read_text()
            jinja = ports.get("jinja")
            html = await jinja(content=template, context={"key": key})
            compile_port = ports.get("compile")
            projection = await compile_port(text=html, context={})
            print(json.dumps(projection, default=str))
            return

    doc = ports.get("document")
    result = await doc.render(state={"key": key})
    print(result)
