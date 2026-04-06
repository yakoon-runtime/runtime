const windows = new Map();

let zIndex = 1;

function getOrCreateWindow(jobId) {
    let win = windows.get(jobId);

    if (!win) {
        win = createWindow(jobId);
        windows.set(jobId, win);
    }

    return win;
}

function createWindow(jobId) {
    const el = document.createElement("div");
    el.className = "window";
    el.style.position = "absolute";
    el.style.left = `${50 + windows.size * 20}px`;
    el.style.top = `${50 + windows.size * 20}px`;
    el.style.width = "400px";
    el.style.height = "300px";
    el.style.border = "1px solid #0e48bb";
    el.style.background = "#fff";
    el.style.overflow = "auto";
    el.style.zIndex = zIndex++;

    makeDraggable(el);

    const content = document.createElement("div");
    content.className = "content";

    el.appendChild(content);

    document.getElementById("canvas").appendChild(el);

    return content;
}

function makeDraggable(el) {
    let offsetX = 0;
    let offsetY = 0;
    let dragging = false;

    el.addEventListener("mousedown", (e) => {
        dragging = true;

        // Fokus + nach vorne
        el.style.zIndex = zIndex++;

        offsetX = e.clientX - el.offsetLeft;
        offsetY = e.clientY - el.offsetTop;
    });

    document.addEventListener("mousemove", (e) => {
        if (!dragging) return;

        el.style.left = (e.clientX - offsetX) + "px";
        el.style.top = (e.clientY - offsetY) + "px";
    });

    document.addEventListener("mouseup", () => {
        dragging = false;
    });
}