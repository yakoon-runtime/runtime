from ..core import is_element, is_whitespace


def map_fields(mapper, node):
    fields = []

    for child in node.children:
        if is_whitespace(child):
            continue

        if not is_element(child, "field"):
            raise ValueError("<fields> can only contain <field>")

        fields.append(map_field(mapper, child))

    name = node.attrs.get("name")

    return {"type": "fields", "name": name, "fields": fields}


def map_field(mapper, node):
    policy = node.attrs.get("policy")
    if not policy:
        raise ValueError("<field> requires 'policy'")

    name = node.attrs.get("name")
    required = node.attrs.get("required", "false").lower() == "true"
    title = node.attrs.get("title")
    lookup = node.attrs.get("lookup")
    hint = node.attrs.get("hint")
    default = node.attrs.get("default")

    return {
        "type": "field",
        "policy": policy,
        "name": name,
        "required": required,
        "title": title,
        "lookup": lookup,
        "hint": hint,
        "default": default,
    }
