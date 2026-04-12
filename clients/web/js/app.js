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
    const renderers = new Map();

    function handleProjection(payload) {

        const regionId = payload.context.origin
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
    }

    const ws = createWS(handleProjection);
    const dispatch = createDispatcher(ws, regionIndex, dom, createRootRegion);

    wireCommandBar(dom, dispatch, createRootRegion);

    function createRootRegion() {
        const container = document.createElement("div");
        container.className = "turn";

        const region = document.createElement("div");

        const regionId = "r-" + crypto.randomUUID();
        region.dataset.regionId = regionId;

        regionIndex.set(regionId, region);

        container.appendChild(region);
        dom.stream.appendChild(container);

        return region;
    }


}

function scrollToBottom() {
    const el = document.getElementById("stream");
    if (!el) return;

    //el.scrollTop = el.scrollHeight;
    el.lastElementChild?.scrollIntoView({ behavior: "smooth" });
}

function createDispatcher(ws, regionIndex, dom, createRootRegion) {

    function send(command, payload = {}, regionEl) {
        const regionId = regionEl.dataset.regionId;

        ws.send(JSON.stringify({
            type: "input",
            channel: "command",
            payload: {
                raw: command,
                context: {
                    command,
                    origin: regionId,
                }
            }
        }));
    }

    function newTurn(command) {
        const regionEl = createRootRegion();
        send(command, {}, regionEl);
    }

    return {
        command: send,
        newTurn
    };
}

function wireCommandBar(dom, dispatch, createRootRegion) {

    function send() {
        const value = dom.input.value;
        if (!value) return;

        const regionEl = createRootRegion();

        dispatch.command(value, {}, regionEl);

        dom.input.value = "";
        scrollToBottom();
    }

    dom.input.addEventListener("keydown", (e) => {
        if (e.key === "Enter") send();
    });

    dom.button.addEventListener("click", send);
}

/* Start Application */
initApp();