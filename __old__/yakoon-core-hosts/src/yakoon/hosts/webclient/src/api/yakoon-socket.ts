let socket: WebSocket | null = null;
let reconnectTimer: ReturnType<typeof setTimeout> | null = null;


export function initYakoonSocket(onMessage: (msg: string) => void) {
  const connect = () => {
    socket = new WebSocket("ws://localhost:8000/ws");

    socket.onopen = () => {
      console.log("[Yakoon] WebSocket verbunden");
      if (reconnectTimer) {
        clearTimeout(reconnectTimer);
        reconnectTimer = null;
      }
    };

    socket.onmessage = (event) => {
      onMessage(event.data);
    };

    socket.onclose = () => {
      console.warn("[Yakoon] Verbindung verloren – versuche Reconnect...");
      reconnectTimer = setTimeout(connect, 2000);
    };

    socket.onerror = () => {
      console.error("[Yakoon] Fehler im Socket – schließe Verbindung");
      socket?.close();
    };
  };

  connect();
}

export function sendToYakoon(message: string) {
  if (socket?.readyState === WebSocket.OPEN) {
    socket.send(message);
  } else {
    console.warn("WebSocket nicht verbunden");
  }
}
