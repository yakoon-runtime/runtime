// =========================
// Renderer
// =========================

class Renderer {
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

            // -------------------------
            // TEXT
            // -------------------------
            if (node.type === "text") {
                dom = document.createElement("div");
                renderTextContent(node.props.text, dom);
            }

            // -------------------------
            // LIST
            // -------------------------
            else if (node.type === "list") {
                dom = document.createElement("ul");
            }

            // -------------------------
            // LIST ITEM
            // -------------------------
            else if (node.type === "list_item") {
                dom = document.createElement("li");
                renderTextContent(node.props.head, dom);
            }

            // -------------------------
            // RULE
            // -------------------------
            else if (node.type === "rule") {
                dom = document.createElement("hr");
            }

            // -------------------------
            // FALLBACK
            // -------------------------
            else {
                dom = document.createElement("div");
            }

            el.appendChild(dom);
            this.renderNode(id, dom);
        }
    }
}

// =========================
// Inline Rendering
// =========================

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

    // String
    if (typeof text === "string") {
        container.textContent = text;
        return;
    }

    // Inline[]
    for (const inline of text) {
        container.appendChild(renderInline(inline));
    }
}


// =========================
// Renderer Mapping
// =========================
/*
const renderers = {
    commands: new Renderer(document.getElementById("commands")),
    chat: new Renderer(document.getElementById("chat")),
};
*/

const renderers = new Map();

function routeProjection(jobId) {
    let r = renderers.get(jobId);

    if (!r) {
        const container = getOrCreateWindow(jobId);

        // 
        r = new Renderer(container);

        renderers.set(jobId, r);
    }

    return r;
}

// =========================
// WebSocket
// =========================

const ws = new WebSocket("ws://localhost:8765");

ws.onopen = () => {
    ws.send(JSON.stringify({ type: "connect" }));

    ws.send(JSON.stringify({
        type: "input",
        channel: "command",
        payload: { text: "welcome" } // man
    }));
};

ws.onmessage = (msg) => {
    const data = JSON.parse(msg.data);

    if (data.type === "projection") {
        const r = routeProjection(data.payload.id);
        r.apply(data.payload);
    }
};


// =========================
// Input (Command Bar)
// =========================

function sendCommand() {
    const input = document.getElementById("command-input");
    const text = input.value;

    if (!text) return;

    ws.send(JSON.stringify({
        type: "input",
        channel: "command",
        payload: { text }
    }));

    input.value = "";
}

document.getElementById("command-input")
    ?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            sendCommand();
        }
    });