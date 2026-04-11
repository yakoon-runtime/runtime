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
    context = payload.get("context") or {}

    return InputEvent.from_raw(
        raw=payload.get("raw"),
        context=InputContext(
            origin=context.get("origin"),
        ),
    )
