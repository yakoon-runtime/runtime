def apply_projection(payload):
    patch = payload["patch"]

    for op in patch["ops"]:
        handle_op(op)

    if patch["final"]:
        render()


nodes = {}
children = {}


def handle_op(op):
    t = op["op"]

    if t == "reset":
        nodes.clear()
        children.clear()

    elif t == "append_structure":
        for n in op["nodes"]:
            nid = n["id"]
            nodes[nid] = n

            parent = n["parent"]
            if parent:
                children.setdefault(parent, []).append(nid)

    elif t == "append_text":
        nid = op["block_id"]
        key = op["key"]
        text = op["text"]

        nodes[nid]["props"][key] = text


def render():
    print("\n--- RENDER ---")

    root = next(iter(nodes.values()))["parent"]  # hacky root
    render_node(root, 0)


def render_node(node_id, indent):
    if node_id not in children:
        return

    for child_id in children[node_id]:
        node = nodes[child_id]
        t = node["type"]
        props = node["props"]

        prefix = "  " * indent

        if t == "text":
            print(prefix + props.get("text", ""))

        elif t == "list_item":
            print(prefix + "- " + props.get("head", ""))

        elif t == "list":
            pass  # container

        render_node(child_id, indent + 1)
