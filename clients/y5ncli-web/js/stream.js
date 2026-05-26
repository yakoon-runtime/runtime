
export function createWS(onProjection) {

    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${protocol}://${window.location.host}/ws`);

    ws.onopen = () => {
        ws.send(JSON.stringify({ type: "connect" }));
    };

    ws.onmessage = (msg) => {
        const data = JSON.parse(msg.data);

        if (data.type === "projection") {
            onProjection(data.payload);
        }
    };

    return ws;
}