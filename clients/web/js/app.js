import { createWS } from "./stream.js";
import { Renderer } from "./renderer.js";
import { createElement } from "./dom.js";


function initApp() {

    const dom = {
        app: document.getElementById("app"),
        stream: document.getElementById("stream"),
        input: document.getElementById("commandbar-input"),
        button: document.getElementById("commandbar-button"),
        sidebar: document.getElementById("toggle-sidebar"),
    };

    function handleProjection(payload) {

        const regionId = payload.context.origin;

        const regionEl = document.querySelector(`[data-region-id="${regionId}"]`);
        if (!regionEl) {
            console.warn("Stale response dropped:", regionId);
            return;
        }

        let renderer = regionEl._renderer;
        if (!renderer) {
            renderer = new Renderer(regionEl, dispatch);
            regionEl._renderer = renderer;
            regionEl.dataset.renderer = "true";
        }

        renderer.apply(payload);
    }

    const ws = createWS(handleProjection);
    const dispatch = createDispatcher(ws, createRootRegion);

    wireCommandBar(dom, dispatch, createRootRegion);
    registerSideBarToggle(dom);

    function createRootRegion() {
        const container = createElement("div", "turn");

        const region = createElement("div", "turn-region");
        region.dataset.regionId = "r-" + crypto.randomUUID();

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

function createDispatcher(ws, createRootRegion) {

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

function registerSideBarToggle(dom) {
    dom.sidebar.onclick = () => {
        dom.app.classList.toggle("sidebar-collapsed");
    };
}

initApp();