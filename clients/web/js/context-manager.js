import { getOrCreateWindow } from "./windows.js";
import { Renderer } from "./renderer.js";

const contexts = new Map();
let activeContextId = null;

export function getOrCreateContext(contextId) {
    let ctx = contexts.get(contextId);

    if (!ctx) {
        const win = getOrCreateWindow(contextId);

        ctx = {
            id: contextId,
            root: win.root,
            container: win.content,
            renderer: new Renderer(win.content),
        };

        // Close-Logik
        win.closeBtn.addEventListener("click", () => {
            removeContext(contextId);
        });

        contexts.set(contextId, ctx);
    }

    return ctx;
}

export function removeContext(contextId) {
    const ctx = contexts.get(contextId);
    if (!ctx) return;

    // DOM entfernen
    ctx.root.remove();

    // aus Map löschen
    contexts.delete(contextId);

    // ggf. active reset
    if (activeContextId === contextId) {
        activeContextId = null;
    }
}

// ==================
// CONTEXT
// ==================

export function setActiveContext(contextId) {
    activeContextId = contextId;
}

export function getActiveContext() {
    return activeContextId;
}

export function clearActiveContext() {
    activeContextId = null;

    document.querySelectorAll(".window").forEach(w => {
        w.classList.remove("active");
    });
}