export class Renderer {

    constructor(container, dispatch, contextId, contextManager) {
        this.container = container;
        this.dispatch = dispatch;
        this.contextId = contextId;
        this.contextManager = contextManager;
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

        const root = Object.values(this.nodes).find(n =>
            n.parent?.endsWith(":root")
        );

        if (!root) return;

        // IMMER diesen Container kontrollieren
        this.container.innerHTML = "";
        this.renderNode(root.parent, this.container, this.contextId);
    }

    renderNode(parentId, el, currentContextId) {

        const kids = this.children[parentId] || [];

        for (const id of kids) {
            const node = this.nodes[id];

            // Block-Wrapper
            const blockEl = document.createElement("div");
            blockEl.className = "block";

            const contentEl = document.createElement("div");
            contentEl.className = "block-content";

            const regionEl = document.createElement("div");
            regionEl.className = "block-region";

            blockEl.appendChild(contentEl);
            blockEl.appendChild(regionEl);

            let dom;
            let nextContextId = currentContextId;

            // CONTEXT-ENTSCHEIDUNG ZENTRAL

            if (node.type === "fields") {

                // eigener Context für Fields
                nextContextId = createSubContextId(currentContextId, "field", node.id);
                this.contextManager.register(nextContextId, regionEl, {
                    type: "field"
                });

            } else if (node.type === "actions") {

                // Field-Regel
                const meta = this.contextManager.getMeta(currentContextId);
                const isField = meta?.type === "field";

                if (!isField) {
                    nextContextId = createSubContextId(currentContextId, "actions", node.id);
                    this.contextManager.register(nextContextId, regionEl, {
                        type: "actions"
                    });
                }
            }

            // RENDERN (mit finalem Context)
            if (node.type === "text") {
                dom = document.createElement("div");
                renderTextContent(node.props.text, this.dispatch, dom, nextContextId);

            } else if (node.type === "fields") {
                dom = renderFields(node, this.dispatch, nextContextId, this.contextManager);

            } else if (node.type === "actions") {
                dom = renderActions(node, this.dispatch, nextContextId, this.contextManager);

            } else if (node.type === "list") {
                dom = document.createElement("ul");

            } else if (node.type === "list_item") {
                dom = document.createElement("li");
                renderTextContent(node.props.head, this.dispatch, dom, nextContextId);

            } else if (node.type === "rule") {
                dom = document.createElement("hr");

            } else {
                dom = document.createElement("div");
            }

            // Content geht in contentEl
            contentEl.appendChild(dom);

            // Block in Tree
            el.appendChild(blockEl);

            // Context sauber weitergeben
            this.renderNode(id, contentEl, nextContextId);
        }
    }

}

// helpers

function renderInline(inline, dispatch, contextId) {
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


        el.onclick = () => {
            dispatch.command(inline.command, inline.payload || {}, contextId);
        };

        return el;
    }

    return document.createTextNode("[unknown inline]");
}

function renderTextContent(text, dispatch, container, contextId) {
    if (!text) return;

    container.style.whiteSpace = "pre-wrap";

    if (typeof text === "string") {
        container.textContent = text;
        return;
    }

    for (const inline of text) {
        container.appendChild(renderInline(inline, dispatch, contextId));
    }
}

function renderFields(node, dispatch, contextId, contextManager) {
    const wrapper = document.createElement("div");
    wrapper.className = "fields";

    for (const field of node.props.fields || []) {

        const fieldBlock = document.createElement("div");
        fieldBlock.className = "field-block";

        const content = document.createElement("div");
        const region = document.createElement("div");
        region.className = "field-region";

        // --- UI ---
        const row = document.createElement("div");
        row.className = "field";

        const label = document.createElement("label");
        label.textContent = field.title || field.var || "";
        row.appendChild(label);

        const inputWrap = document.createElement("div");
        inputWrap.className = "input-wrap";

        const input = document.createElement("input");
        input.value = field.query ?? field.default ?? "";
        input.placeholder = field.hint || "";

        inputWrap.appendChild(input);

        // Lookup integriert
        if (field.lookup) {
            inputWrap.classList.add("has-lookup");

            const icon = document.createElement("span");
            icon.className = "lookup-icon";
            icon.textContent = "▾";

            icon.onclick = () => {
                // jetzt automatisch den richtigen Context
                dispatch.command(field.lookup, {}, contextId);
            };

            inputWrap.appendChild(icon);
        }

        row.appendChild(inputWrap);

        if (field.errors?.length) {
            const err = document.createElement("div");
            err.className = "field-error";
            err.textContent = field.errors[0].message;
            row.appendChild(err);
        }

        content.appendChild(row);

        fieldBlock.appendChild(content);
        fieldBlock.appendChild(region);

        wrapper.appendChild(fieldBlock);
    }

    return wrapper;
}

function renderActions(node, dispatch, contextId, contextManager) {

    const wrapper = document.createElement("div");

    for (const action of node.props.actions || []) {
        const btn = document.createElement("button");
        btn.textContent = action.label;

        btn.onclick = () => {
            dispatch.command(action.command, {}, contextId);
        };

        wrapper.appendChild(btn);
    }

    // optionaler Container für spätere Inhalte (kein Context!)
    const region = document.createElement("div");
    wrapper.appendChild(region);

    return wrapper;
}

function createSubContextId(parent, type, nodeId) {
    return [parent, type, nodeId].join("::");
}