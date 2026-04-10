export class Renderer {

    constructor(container, dispatch, regionIndex) {
        this.container = container;
        this.dispatch = dispatch;
        this.regionIndex = regionIndex;

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
        this.renderNode(root.parent, this.container);
    }

    renderNode(parentId, el) {

        const kids = this.children[parentId] || [];

        for (const id of kids) {
            const node = this.nodes[id];

            const blockEl = document.createElement("div");
            blockEl.className = "block";

            const contentEl = document.createElement("div");
            contentEl.className = "block-content";

            const regionEl = document.createElement("div");
            regionEl.className = "block-region";

            // Region-ID erzeugen
            const regionId = "r-" + crypto.randomUUID();
            regionEl.dataset.regionId = regionId;

            // registrieren
            this.regionIndex.set(regionId, regionEl);

            blockEl.appendChild(contentEl);
            blockEl.appendChild(regionEl);

            let dom;

            if (node.type === "text") {
                dom = document.createElement("div");
                renderTextContent(node.props.text, this.dispatch, dom, regionEl);

            } else if (node.type === "fields") {
                dom = renderFields(node, this.dispatch, regionEl, this.regionIndex);

            } else if (node.type === "actions") {
                dom = renderActions(node, this.dispatch, regionEl);

            } else if (node.type === "list") {
                dom = document.createElement("ul");

            } else if (node.type === "list_item") {
                dom = document.createElement("li");
                renderTextContent(node.props.head, this.dispatch, dom, regionEl);

            } else if (node.type === "rule") {
                dom = document.createElement("hr");

            } else {
                dom = document.createElement("div");
            }

            contentEl.appendChild(dom);
            el.appendChild(blockEl);

            // Kinder laufen im content weiter
            this.renderNode(id, contentEl);
        }
    }

}

// helpers

function findRegion(el) {
    if (!(el instanceof Element)) {
        return null;
    }
    return el.closest("[data-region-id]");
}


// RENDERER

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

function renderTextContent(text, dispatch, container, regionEl) {
    if (!text) return;

    container.style.whiteSpace = "pre-wrap";

    if (typeof text === "string") {
        container.textContent = text;
        return;
    }

    for (const inline of text) {
        container.appendChild(renderInline(inline, dispatch, regionEl));
    }
}

function renderFields(node, dispatch, parentRegionEl, regionIndex) {

    const wrapper = document.createElement("div");
    wrapper.className = "fields";

    for (const field of node.props.fields || []) {

        const fieldBlock = document.createElement("div");
        fieldBlock.className = "field-block";

        const region = document.createElement("div");
        region.className = "field-region";

        const regionId = "r-" + crypto.randomUUID();
        region.dataset.regionId = regionId;
        regionIndex.set(regionId, region);

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

        if (field.lookup) {
            const icon = document.createElement("button");
            icon.className = "lookup-icon";
            icon.type = "button";
            icon.textContent = "▾";

            icon.onclick = () => {
                dispatch.command(field.lookup, {}, region);
            };

            inputWrap.appendChild(icon);
        }

        row.appendChild(inputWrap);

        // direkt anhängen
        fieldBlock.appendChild(row);
        fieldBlock.appendChild(region);

        wrapper.appendChild(fieldBlock);
    }

    return wrapper;
}


function renderActions(node, dispatch, regionEl) {


    const wrapper = document.createElement("div");

    for (const action of node.props.actions || []) {
        const btn = document.createElement("button");
        btn.textContent = action.label;

        btn.onclick = (e) => {
            const region = findRegion(e.currentTarget)

            if (!region) {
                console.warn("No region found for action");
                return;
            }
            dispatch.command(action.command, {}, region);
        };

        wrapper.appendChild(btn);
    }

    return wrapper;
}
