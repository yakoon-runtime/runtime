import { createWS } from "./stream.js";
import { createContextManager } from "./context-manager.js";
import { createRouter } from "./projection-router.js";


function initApp() {

    const dom = {
        stream: document.getElementById("stream"),
        input: document.getElementById("commandbar-input"),
        button: document.getElementById("commandbar-button"),
    };

    function handleProjection(payload) {

        const contextId = router.resolve(payload);

        // Fallback
        if (!contextId) {
            console.warn("Fallback context used for projection", payload.id);
        }

        const ctx = contextManager.getOrCreate(contextId);
        ctx.renderer.apply(payload);
        scrollToBottom();
    }

    const ws = createWS(handleProjection);
    const dispatch = createDispatcher(ws);
    const contextManager = createContextManager(dom.stream, dispatch);
    const router = createRouter();

    wireCommandBar(dom, dispatch, contextManager);
}

function scrollToBottom() {
    const el = document.getElementById("stream");
    if (!el) return;

    //el.scrollTop = el.scrollHeight;
    el.lastElementChild?.scrollIntoView({ behavior: "smooth" });
}

function createDispatcher(ws) {
    function send(command, payload = {}, contextId) {

        console.log("SEND", command);
        ws.send(JSON.stringify({
            type: "input",
            channel: "command",
            payload: {
                raw: command,
                context: {
                    context_id: contextId,
                    command
                }
            }
        }));
    }

    return {
        command: send
    };
}

function wireCommandBar(dom, dispatch, contextManager) {

    function createNewContextId() {
        return "ctx-" + Date.now();
    }

    function send() {
        const value = dom.input.value;
        if (!value) return;

        const contextId =
            contextManager.getActive() ||
            createNewContextId();

        dispatch.command(value, {}, contextId);

        dom.input.value = "";
    }

    dom.input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") send();
    });

    dom.button.addEventListener("click", send);
}

/* Start Application */
initApp();