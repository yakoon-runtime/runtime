from y5n.sdk import context, io, session


async def main():
    rows = await session.list()
    current_key = context.session().key
    current = next((r for r in rows if r["key"] == current_key), None)

    if current:
        await io.write(f"Session:  {current_key}")
        await io.write(
            f"clients={current['clients']}  homes={current['homes']}  flows={current['flows']}"
        )
    else:
        await io.write(f"Session:  {current_key}")
