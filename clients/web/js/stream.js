
export function createWS(onProjection) {
    const ws = new WebSocket("ws://localhost:8765");

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