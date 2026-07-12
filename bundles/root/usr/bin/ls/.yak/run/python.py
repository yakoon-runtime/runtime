from pathlib import Path

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text


async def run(space: NodeSpace):

    target_name = space.request.arg(0)
    use_list = space.request.has_option("l")

    cwd_raw = space.session.get_data("fs:cwd")
    if not cwd_raw:
        cwd_raw = space.session.get_data("fs:root", "")
    cwd = Path(cwd_raw) if cwd_raw else Path.home() / ".yak"

    if target_name:
        if target_name.startswith("/"):
            raw_root = space.session.get_data("fs:root", "")
            target = (Path(raw_root) / target_name.lstrip("/")) if raw_root else Path(target_name)
        else:
            target = cwd / target_name
    else:
        target = cwd

    target = target.resolve()

    if not target.exists():
        yield out(to_text(f"Not found: {target}"))
        return

    if not target.is_dir():
        yield out(to_text(target.name))
        return

    entries = sorted(target.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
    items = [f"{p.name}/" if p.is_dir() else p.name for p in entries]

    if use_list:
        yield out(to_text("\n".join(items)))
    else:
        yield out(to_text("  ".join(items)))
