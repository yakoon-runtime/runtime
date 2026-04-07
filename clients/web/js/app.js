import { Renderer } from "./renderer.js";
import { resolveContext } from "./projection-router.js";
import { getOrCreateContext, getActiveContext } from "./context-manager.js";

// =========================
// QUERY UI-Parts
// =========================

const sidebar = document.getElementById("sidebar");
const toggleBtn = document.getElementById("toggle-sidebar");


// =========================
// WebSocket
// =========================

const ws = new WebSocket("ws://localhost:8765");

ws.onopen = () => {
    ws.send(JSON.stringify({ type: "connect" }));

    // initial command
    ws.send(createInputEvent("welcome", "ctx-1"));
};

ws.onmessage = (msg) => {
    const data = JSON.parse(msg.data);

    if (data.type === "projection") {
        handleProjection(data.payload);
    }
};

// =========================
// Projection Handling
// =========================

function handleProjection(payload) {
    const contextId = resolveContext(payload);

    if (!contextId) {
        console.warn("No context for projection:", payload.id);
        return;
    }

    const ctx = getOrCreateContext(contextId);

    ctx.renderer.apply(payload);
}

// =========================
// Input (Command Bar)
// =========================

function sendCommand() {
    const input = document.getElementById("commandbar-input");
    if (!input) {
        console.error("Input not found");
        return;
    }

    const text = input.value;
    if (!text) return;

    let contextId = getActiveContext();

    if (!contextId) {
        contextId = createNewContextId();
    }

    ws.send(createInputEvent(text, contextId));

    input.value = "";
}

function createNewContextId() {
    return "ctx-" + Date.now();
}

function createInputEvent(command, context_id) {
    return JSON.stringify({
        type: "input",
        channel: "command",
        payload: {
            raw: command,
            context: {
                command: command,
                context_id: context_id
            }
        }
    });
}

document.getElementById("commandbar-input")
    ?.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            sendCommand();
        }
    });




document.getElementById("toggle-sidebar")
    .addEventListener("click", () => {
        console.log(sidebar.classList);
        sidebar.classList.toggle("hidden");
    });


document.getElementById("commandbar-button")
    .addEventListener("click", sendCommand);