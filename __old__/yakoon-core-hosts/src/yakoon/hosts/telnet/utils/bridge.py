from y5n.hosts.telnet.utils.ansi import format_codes_to_ansi
from y5n.runtime.machine.directories import Engine, Output

engine = Engine(None)


async def handle_client(reader, writer):

    async def out(msg: str):
        msg_str = format_codes_to_ansi(str(msg))
        writer.write((msg_str + "\r\n").encode("utf-8"))
        await writer.drain()

    addr = writer.get_extra_info("peername")
    session_id = f"{addr[0]}:{addr[1]}"
    print(f"[Telnet] Verbindung von {session_id}")

    await engine.initialize(Output(out, out))

    while True:
        command = await reader.readline()
        if not command:
            continue
        command = command.decode("utf-8").strip()
        await engine.dispatch(session_id, command, Output(out, out))
