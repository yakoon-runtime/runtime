import { createWS } from "./stream.js";
import { Renderer } from "./renderer.js";


function initApp() {

    const dom = {
        stream: document.getElementById("stream"),
        input: document.getElementById("commandbar-input"),
        button: document.getElementById("commandbar-button"),
    };

    // zentrale Maps
    const regionIndex = new Map();
    const pendingJobs = new Map();
    const renderers = new Map();

    function handleProjection(payload) {

        //const regionId = pendingJobs.get(payload.job);
        const regionId = pendingJobs.get(payload.context.context_id);

        const regionEl = regionIndex.get(regionId);

        if (!regionEl) {
            console.warn("Region not found for job:", payload.job);
            return;
        }

        //  Renderer holen oder erstellen
        let renderer = renderers.get(regionId);

        if (!renderer) {
            renderer = new Renderer(regionEl, dispatch, regionIndex);
            renderers.set(regionId, renderer);
        }

        renderer.apply(payload);

        if (payload.final) {
            pendingJobs.delete(payload.job);
        }
    }

    const ws = createWS(handleProjection);
    const dispatch = createDispatcher(ws, regionIndex, pendingJobs);

    wireCommandBar(dom, dispatch, regionIndex);
}

function scrollToBottom() {
    const el = document.getElementById("stream");
    if (!el) return;

    //el.scrollTop = el.scrollHeight;
    el.lastElementChild?.scrollIntoView({ behavior: "smooth" });
}

function createDispatcher(ws, regionIndex, pendingJobs) {

    function send(command, payload = {}, regionEl) {

        const regionId = regionEl?.dataset.regionId;
        const jobId = crypto.randomUUID();

        // 🔥 merken
        pendingJobs.set(jobId, regionId);

        console.log("SEND", command);

        ws.send(JSON.stringify({
            type: "input",
            channel: "command",
            payload: {
                raw: command,
                context: {
                    context_id: jobId,
                    command
                }
            }
        }));
    }

    return {
        command: send
    };
}

function wireCommandBar(dom, dispatch, regionIndex) {

    function createRootBlock() {

        const blockEl = document.createElement("div");
        blockEl.className = "block";

        const contentEl = document.createElement("div");
        contentEl.className = "block-content";

        const regionEl = document.createElement("div");
        regionEl.className = "block-region";

        // 🔥 regionId
        const regionId = "r-" + crypto.randomUUID();
        regionEl.dataset.regionId = regionId;

        regionIndex.set(regionId, regionEl);

        blockEl.appendChild(contentEl);
        blockEl.appendChild(regionEl);

        dom.stream.appendChild(blockEl);

        return regionEl;
    }

    function send() {
        const value = dom.input.value;
        if (!value) return;

        const regionEl = createRootBlock();

        dispatch.command(value, {}, regionEl);

        dom.input.value = "";
    }

    dom.input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") send();
    });

    dom.button.addEventListener("click", send);
}

/* Start Application */
initApp();