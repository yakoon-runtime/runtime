from ..core import extract_text, is_element, is_whitespace


def map_actions(mapper, node):
    actions = []

    for child in node.children:
        if is_whitespace(child):
            continue

        if not is_element(child, "action"):
            raise ValueError("<actions> can only contain <action>")

        actions.append(map_action(mapper, child))

    return {"type": "actions", "actions": actions}


def map_action(mapper, node):
    command = node.attrs.get("command")
    if not command:
        raise ValueError("<action> requires 'command' attribute")

    label = extract_text(node).strip()
    if not label:
        raise ValueError("<action> requires label text")

    scope = node.attrs.get("scope")

    return {"type": "action", "label": label, "scope": scope, "command": command}
