import asyncio
import uuid

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from y5n.runtime.machine.directories import Engine, Output

engine = Engine(None)

router = APIRouter()
active_sessions = {}


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):

    await websocket.accept()
    session_id = f"ws-{uuid.uuid4().hex[:6]}"

    print(f"[WebSocket] Connected: {session_id}")

    out = err = websocket.send_text
    output = Output(out, err)

    try:
        await engine.initialize(output)
        while True:
            await asyncio.sleep(0.1)
            command = await websocket.receive_text()

            await engine.dispatch(session_id, command, output)

    except WebSocketDisconnect:
        print(f"[WebSocket] Disconnected: {session_id}")
        # hier ggf. cleanup z. B. session schließen
