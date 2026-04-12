export class Renderer {

    constructor(container, dispatch) {
        this.container = container;
        this.dispatch = dispatch;

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

        this.container.innerHTML = "";
        this.renderNode(root.parent, this.container);
    }

    renderNode(parentId, container) {
        const kids = this.children[parentId] || [];

        for (const id of kids) {
            const node = this.nodes[id];

            const el = this.createElement(node);
            container.appendChild(el);

            // Kinder direkt in dieses Element rendern
            this.renderNode(id, el);
        }
    }

    createElement(node) {
        let el;

        switch (node.type) {

            case "text":
                el = document.createElement("div");
                renderTextContent(node.props.text, this.dispatch, el);
                break;

            case "fields":
                el = renderFields(node, this.dispatch);
                break;

            case "actions":
                el = renderActions(node, this.dispatch);
                break;

            case "list":
                el = document.createElement("ul");
                break;

            case "list_item":
                el = document.createElement("li");
                renderTextContent(node.props.text, this.dispatch, el);
                break;

            case "rule":
                el = document.createElement("hr");
                break;

            default:
                el = document.createElement("div");
        }

        return el;
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

function renderInline(inline, dispatch, regionEl) {

    function createInlineEl(type, tag = "span") {
        const el = document.createElement(tag);
        el.classList.add("inline", `inline-${type}`);
        return el;
    }

    if (inline.type === "text") {
        return document.createTextNode(inline.text);
    }

    if (inline.type === "code") {
        const el = createInlineEl("code", "code");

        el.textContent = inline.text;
        return el;
    }

    if (inline.type === "cmd") {
        const el = createInlineEl("cmd");

        el.textContent = inline.text;
        el.onclick = () => {
            dispatch.newTurn(inline.command);
        }
        return el;
    }

    if (inline.type === "select") {
        const el = createInlineEl("select");

        el.textContent = inline.text;

        el.onclick = () => {
            const field = el.closest(".field-block");
            if (!field) {
                console.warn("Select outside field-block");
                return;
            }

            const input = field.querySelector("input");
            if (!input) return;

            // 1. sichtbarer Text
            input.value = inline.text;

            // 2. echter Wert
            field.dataset.value = inline.value;

            // 3. Lookup schließen
            const region = el.closest("[data-region-id]");
            if (region) region.innerHTML = "";
        };

        return el;
    }

    if (inline.type === "action") {
        const el = createInlineEl("action");

        el.textContent = inline.text;
        el.onclick = () => {
            const region = findRegion(el);
            if (!region) return;

            dispatch.command(inline.command, inline.payload || {}, region);
        };

        return el;
    }

    return document.createTextNode("[unknown inline]");
}

function renderTextContent(text, dispatch, container) {
    if (!text) return;

    container.style.whiteSpace = "pre-wrap";

    if (typeof text === "string") {
        container.textContent = text;
        return;
    }

    for (const inline of text) {
        container.appendChild(renderInline(inline, dispatch, container));
    }
}

function renderFields(node, dispatch) {
    const wrapper = document.createElement("div");
    wrapper.className = "fields";

    for (const field of node.props.fields || []) {

        const fieldBlock = document.createElement("div");
        fieldBlock.className = "field-block";

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

        // 👉 Region NUR hier
        const region = document.createElement("div");
        region.className = "field-region";

        const regionId = "r-" + crypto.randomUUID();
        region.dataset.regionId = regionId;

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

        fieldBlock.appendChild(row);
        fieldBlock.appendChild(region);

        wrapper.appendChild(fieldBlock);
    }

    return wrapper;
}

function renderActions(node, dispatch) {
    const wrapper = document.createElement("div");
    wrapper.className = "actions";

    for (const action of node.props.actions || []) {
        const btn = document.createElement("button");
        btn.textContent = action.label;

        btn.onclick = (e) => {
            const region = findRegion(e.currentTarget);
            if (!region) return;

            dispatch.command(action.command, {}, region);
        };

        wrapper.appendChild(btn);
    }

    return wrapper;
}