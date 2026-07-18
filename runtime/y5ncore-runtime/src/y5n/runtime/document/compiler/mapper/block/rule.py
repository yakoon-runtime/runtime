from y5n.base.document.model import RuleBlock


def map_rule(mapper, node):
    style = node.attrs.get("style", "normal")

    if style not in ("subtle", "normal", "strong"):
        raise ValueError(
            f"Invalid rule style: {style!r}. Expected one of ('subtle','normal','strong')"
        )

    return RuleBlock(
        type="rule",
        id=None,
        style=style,
    )
