import { Renderer } from "./renderer.js";

const contexts = new Map();
let activeContextId = null;

const stream = document.getElementById("stream");

export function getOrCreateContext(contextId) {
    let ctx = contexts.get(contextId);

    if (!ctx) {
        const container = document.createElement("div");
        container.className = "turn";

        stream.appendChild(container);

        ctx = {
            id: contextId,
            container,
            renderer: new Renderer(container),
        };

        contexts.set(contextId, ctx);
    }

    return ctx;
}

// ==================
// CONTEXT (nur logisch)
// ==================

export function setActiveContext(contextId) {
    activeContextId = contextId;
}

export function getActiveContext() {
    return activeContextId;
}

export function clearActiveContext() {
    activeContextId = null;
}