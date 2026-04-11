import { createWS } from "./stream.js";
import { Renderer, createBlock } from "./renderer.js";


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
    const dispatch = createDispatcher(ws, regionIndex, dom);

    wireCommandBar(dom, dispatch, regionIndex);
}

function scrollToBottom() {
    const el = document.getElementById("stream");
    if (!el) return;

    //el.scrollTop = el.scrollHeight;
    el.lastElementChild?.scrollIntoView({ behavior: "smooth" });
}

function createDispatcher(ws, regionIndex, dom) {

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

    function newTurn(command, payload = {}) {
        const { blockEl, regionEl } = createBlock(regionIndex);

        dom.stream.appendChild(blockEl);

        send(command, payload, regionEl);
    }

    return {
        command: send,
        newTurn
    };
}

function wireCommandBar(dom, dispatch, regionIndex) {

    function createRootBlock() {
        const { blockEl, regionEl } = createBlock(regionIndex);

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