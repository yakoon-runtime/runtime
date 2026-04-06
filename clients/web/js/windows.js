import { setActiveContext } from "./context-manager.js";

const windows = new Map();

let zIndex = 1;

export function getOrCreateWindow(contextId) {
    let win = windows.get(contextId);

    if (!win) {
        win = createWindow(contextId);
        windows.set(contextId, win);
    }

    return win;
}

function createWindow(contextId) {
    const root = document.createElement("div");
    root.className = "window";
    root.dataset.context = contextId;

    // dynamische Werte 
    root.style.left = `${50 + windows.size * 20}px`;
    root.style.top = `${50 + windows.size * 20}px`;
    root.style.zIndex = zIndex++;

    // =========================
    // Close Button
    // =========================

    const closeBtn = document.createElement("button");
    closeBtn.className = "window-close";
    closeBtn.textContent = "×";

    // verhindert Fokuswechsel beim Klick
    closeBtn.addEventListener("mousedown", (e) => {
        e.stopPropagation();
    });

    root.appendChild(closeBtn);

    // =========================
    // Content
    // =========================

    const content = document.createElement("div");
    content.className = "content";

    root.appendChild(content);

    // =========================
    // Fokus + Z-Index
    // =========================

    root.addEventListener("mousedown", () => {
        root.style.zIndex = zIndex++;
        setActiveContext(contextId);
        setActiveWindow(contextId);
    });

    // =========================
    // Dragging
    // =========================

    makeDraggable(root);

    // =========================
    // Mount
    // =========================

    document.getElementById("canvas").appendChild(root);

    return {
        id: contextId,
        root,
        content,
        closeBtn
    };
}

// =========================
// Fokus / Active Window
// =========================

export function setActiveWindow(contextId) {
    document.querySelectorAll(".window").forEach(w => {
        w.classList.remove("active");
    });

    const el = document.querySelector(`[data-context="${contextId}"]`);
    if (el) {
        el.classList.add("active");
    }
}

// =========================
// Dragging
// =========================

let activeDrag = null;

function makeDraggable(el) {
    el.addEventListener("mousedown", (e) => {
        activeDrag = {
            el,
            offsetX: e.clientX - el.offsetLeft,
            offsetY: e.clientY - el.offsetTop,
        };
    });
}

document.addEventListener("mousemove", (e) => {
    if (!activeDrag) return;

    const { el, offsetX, offsetY } = activeDrag;

    el.style.left = (e.clientX - offsetX) + "px";
    el.style.top = (e.clientY - offsetY) + "px";
});

document.addEventListener("mouseup", () => {
    activeDrag = null;
});