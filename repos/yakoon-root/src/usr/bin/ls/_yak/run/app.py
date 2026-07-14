from pathlib import Path

from y5n.api.dsl import out
from y5n.api.nodes import NodeSpace
from y5n.api.projections import to_text


async def run(space: NodeSpace):

    target_name = space.request.arg(0)
    use_list = space.request.has_option("l")

    target = _resolve(space, target_name)

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


# ----------------------------
# INTERNALS
# ----------------------------


def _get_root(space: NodeSpace) -> Path:
    raw = space.session.get_data("fs:root")
    return Path(raw) if raw else Path.home() / "_yak"


def _resolve(space: NodeSpace, target_name: str | None) -> Path:
    root = _get_root(space)
    raw = space.session.get_current_path()

    if raw and raw != "/":
        test = root / raw.lstrip("/")
        current = test.resolve() if test.exists() else Path(raw).resolve()
    else:
        current = root.resolve()

    if target_name:
        if target_name == "~":
            return Path.home().resolve()
        if target_name.startswith("/"):
            return (root / target_name.lstrip("/")).resolve()
        return (current / target_name).resolve()
    return current
