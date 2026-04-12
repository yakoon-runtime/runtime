
export function createElement(tag, className) {
    const el = document.createElement(tag);
    if (className) el.classList.add(className);
    return el;
}

export function findRegion(el) {
    if (!(el instanceof Element)) {
        return null;
    }
    return el.closest("[data-region-id]");
}
