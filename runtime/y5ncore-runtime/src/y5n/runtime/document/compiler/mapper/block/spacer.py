def map_spacer(mapper, node):
    raw = node.attrs.get("size", "1")

    try:
        size = int(raw)
    except ValueError as e:
        raise ValueError(f"Spacer size must be an integer, got {raw!r}") from e

    if size < 0:
        raise ValueError("Spacer size must be >= 0")

    return {"type": "spacer", "size": size}
