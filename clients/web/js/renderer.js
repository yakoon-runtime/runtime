export class Renderer {
    constructor(container) {
        this.container = container;
        this.nodes = {};
        this.children = {};
    }

    apply(payload) {
        const patch = payload.patch;

        for (const op of patch.ops) {
            this.handle(op);
        }

        if (patch.final) {
            this.render();
        }
    }

    handle(op) {
        if (op.op === "reset") {
            this.nodes = {};
            this.children = {};
        }

        if (op.op === "append_structure") {
            for (const n of op.nodes) {
                this.nodes[n.id] = n;

                if (n.parent) {
                    if (!this.children[n.parent]) {
                        this.children[n.parent] = [];
                    }
                    this.children[n.parent].push(n.id);
                }
            }
        }

        if (op.op === "append_text") {
            const node = this.nodes[op.block_id];
            node.props[op.key] = op.text;
        }
    }

    render() {
        this.container.innerHTML = "";

        const root = Object.values(this.nodes).find(n =>
            n.parent?.endsWith(":root")
        );

        if (!root) return;

        this.renderNode(root.parent, this.container);
    }

    renderNode(parentId, el) {
        const kids = this.children[parentId] || [];

        for (const id of kids) {
            const node = this.nodes[id];

            let dom;

            if (node.type === "text") {
                dom = document.createElement("div");
                renderTextContent(node.props.text, dom);
            } else if (node.type === "list") {
                dom = document.createElement("ul");
            } else if (node.type === "list_item") {
                dom = document.createElement("li");
                renderTextContent(node.props.head, dom);
            } else if (node.type === "rule") {
                dom = document.createElement("hr");
            } else {
                dom = document.createElement("div");
            }

            el.appendChild(dom);
            this.renderNode(id, dom);
        }
    }
}

// helpers

function renderInline(inline) {
    if (inline.type === "text") {
        return document.createTextNode(inline.text);
    }

    if (inline.type === "code") {
        const el = document.createElement("code");
        el.textContent = inline.code;
        return el;
    }

    if (inline.type === "action") {
        const el = document.createElement("span");
        el.textContent = inline.text;

        el.style.cursor = "pointer";
        el.style.textDecoration = "underline";

        el.onclick = () => {
            ws.send(JSON.stringify({
                type: "input",
                channel: inline.channel,
                payload: inline.payload
            }));
        };

        return el;
    }

    return document.createTextNode("[unknown inline]");
}

function renderTextContent(text, container) {
    if (!text) return;

    container.style.whiteSpace = "pre-wrap";

    if (typeof text === "string") {
        container.textContent = text;
        return;
    }

    for (const inline of text) {
        container.appendChild(renderInline(inline));
    }
}