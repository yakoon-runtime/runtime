import asyncio

from yakoon.apps.telnet.utils.bridge import handle_client


async def run_telnet():

    server = await asyncio.start_server(handle_client, "0.0.0.0", 4000)
    print("✅ Yakoon Telnet läuft auf Port 4000")
    async with server:
        await server.serve_forever()


if __name__ == "__main__":
    asyncio.run(run_telnet())
