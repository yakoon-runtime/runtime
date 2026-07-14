from y5n.api.naming import Key, Namespace


def world_key(world_id: str) -> Key:
    return Key.from_parts("luma", "world", "global", world_id)


def box_key(box_id: str) -> Key:
    return Key.from_parts("luma", "box", "global", box_id)


def exit_key(exit_id: str) -> Key:
    return Key.from_parts("luma", "exit", "global", exit_id)


def note_key(note_id: str) -> Key:
    return Key.from_parts("luma", "note", "global", note_id)


def world_namespace() -> Namespace:
    return Namespace("luma", "world", "global")


def box_namespace() -> Namespace:
    return Namespace("luma", "box", "global")


def exit_namespace() -> Namespace:
    return Namespace("luma", "exit", "global")


def note_namespace() -> Namespace:
    return Namespace("luma", "note", "global")
