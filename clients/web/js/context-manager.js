import { Renderer } from "./renderer.js";
export function createContextManager(streamEl, dispatch) {

    const contexts = new Map();
    let activeContextId = null;

    function register(contextId, el, meta = {}) {
        if (contexts.has(contextId)) {
            return contexts.get(contextId);
        }

        const ctx = {
            id: contextId,
            container: el,
            renderer: new Renderer(el, dispatch, contextId, api),
            meta
        };

        contexts.set(contextId, ctx);
        return ctx;
    }

    function has(contextId) {
        return contexts.has(contextId);
    }

    function getMeta(contextId) {
        return contexts.get(contextId)?.meta;
    }

    function getOrCreate(contextId) {

        if (contexts.has(contextId)) {
            return contexts.get(contextId);
        }

        const container = document.createElement("div");
        container.className = "turn";
        container.dataset.contextId = contextId;

        streamEl.appendChild(container);

        return register(contextId, container);
    }

    const api = {
        has,
        register,
        getOrCreate,
        getMeta,
        getActive() {
            return activeContextId;
        },
        setActive(id) {
            activeContextId = id;
        }
    };

    return api;
}