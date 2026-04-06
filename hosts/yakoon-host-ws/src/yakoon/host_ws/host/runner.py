import json

from yakoon.base.runtime import InputEvent
from yakoon.base.runtime.input.context import InputContext


async def handle(host, connection, ws):

    # --- CONNECT PHASE ---
    msg = await ws.recv()
    data = json.loads(msg)

    session_key = data.get("session")

    await host.connect(connection, session_key=session_key)

    # --- EVENT LOOP ---
    try:
        async for msg in ws:
            data = json.loads(msg)

            # receive simple ping / send pong
            if data.get("type") == "ping":
                await ws.send(json.dumps({"type": "pong"}))
                continue

            if data.get("type") == "input":
                event = map_to_input_event(data)
                await host.receive_input(connection, event)

    finally:
        await host.disconnect(connection)


def map_to_input_event(data):
    payload = data.get("payload", {})

    # --- RAW ---
    raw = payload.get("raw")

    # --- CONTEXT ---
    ctx_data = payload.get("context") or {}

    context = InputContext(
        command=ctx_data.get("command"),
        context_id=ctx_data.get("context_id"),
        open_contexts=[],  # optional später
        ui=ctx_data.get("ui") or {},
    )

    return InputEvent(raw=raw, context=context)
