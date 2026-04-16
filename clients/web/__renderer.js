import { createElement, findRegion, findScope } from "./js/renderer/dom.js";
import { collectFields, buildCommand } from "./js/cmd.js";


export class Renderer {

    static from(el) {
        const root = el.closest('[data-renderer="true"]');
        return root?._renderer || null;
    }

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
                el = createElement("div", "text");
                renderTextContent(node.props.text, this.dispatch, el);
                break;

            case "fields":
                el = createElement("div", "fields");
                renderFields(node, this.dispatch, el);
                break;

            case "actions":
                el = createElement("div", "actions");
                renderActions(node, this.dispatch, el);
                break;

            case "list":
                el = createElement("ul", "list");
                break;

            case "list_item":
                el = createElement("li", "list-item");
                renderTextContent(node.props.text, this.dispatch, el);
                break;

            case "kv":
                el = createElement("div", "kv");
                break;

            case "kv_item":
                el = createElement("div", "kv-item");
                renderKVItem(node, this.dispatch, el);
                break;

            case "rule":
                el = createElement("hr", "rule");
                break;

            default:
                el = document.createElement("div");
        }

        return el;
    }

    openInteraction(region, command) {
        if (region.dataset.open === command) {
            region.innerHTML = "";
            delete region.dataset.open;
            return;
        }

        region.innerHTML = "";
        region.dataset.open = command;

        this.dispatch.command(command, {}, region);
    }

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

    if (typeof text === "string") {
        container.textContent = text;
        return;
    }

    for (const inline of text) {
        container.appendChild(renderInline(inline, dispatch, container));
    }
}

function renderKVItem(node, dispatch, container) {

    const key = createElement("div", "kv-key");
    key.textContent = node.props.key;

    const value = createElement("div", "kv-value");
    renderTextContent(node.props.value, dispatch, value);

    container.appendChild(key);
    container.appendChild(value);
}

function renderFields(node, dispatch, container) {

    if (node.props.name) {
        container.dataset.scope = node.props.name;
    }

    for (const field of node.props.fields || []) {

        const fieldBlock = createElement("div", "field-block");
        const row = createElement("div", "field-row");

        const label = createElement("label", "field-label");
        label.textContent = field.title || field.var || "";

        const inputWrap = createElement("div", "field-wrap");

        const input = createElement("input", "field-input");
        input.name = field.name;
        input.value = field.query ?? field.default ?? "";
        input.placeholder = field.hint || "";

        const region = createElement("div", "field-region");
        region.dataset.regionId = "r-" + crypto.randomUUID();

        inputWrap.appendChild(input);

        if (field.lookup) {
            const icon = createElement("button", "field-lookup");
            icon.textContent = "▾";

            icon.onclick = () => {
                const renderer = Renderer.from(region);
                if (!renderer) return;
                renderer.openInteraction(region, field.lookup);
            };

            inputWrap.appendChild(icon);
        }

        row.appendChild(label);
        row.appendChild(inputWrap);

        fieldBlock.appendChild(row);
        fieldBlock.appendChild(region);

        container.appendChild(fieldBlock);
    }
}

function renderActions(node, dispatch, container) {

    for (const action of node.props.actions || []) {
        const btn = createElement("button", "action-button");
        btn.textContent = action.label;

        btn.onclick = (e) => {
            const region = findRegion(e.currentTarget);
            if (!region) return;

            if (action.scope) {
                const root = findScope(e.currentTarget, action.scope);

                const data = collectFields(root);
                const cmd = buildCommand(action.command, data);
                dispatch.command(cmd, {}, region);
            } else {
                dispatch.command(action.command, {}, region);
            }
        };

        container.appendChild(btn);
    }
}