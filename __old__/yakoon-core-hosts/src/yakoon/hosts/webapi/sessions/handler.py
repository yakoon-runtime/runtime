from y5n.runtime.machine.directories import Engine, Output

# Set the global rendering mode to ansi text (no Markdown formatting)
_engine = Engine(None)


async def handle_input(session_id: str, input_str: str) -> str:
    output: list[str] = []

    async def out(msg: str):
        output.append(str(msg))

    output = Output(out, out)

    await _engine.send(session_id, input_str, output)
    return "\n".join(output)
