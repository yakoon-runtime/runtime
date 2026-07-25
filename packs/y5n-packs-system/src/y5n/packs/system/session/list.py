from y5n.sdk import context, io, session


async def main():
    rows = await session.list()

    if not rows:
        await io.write("No sessions.")
        return

    current_key = context.session().key
    lines = []
    for r in rows:
        marker = "* " if r["key"] == current_key else "  "
        lines.append(
            f"{marker}{r['key']:<45} clients={r['clients']}  homes={r['homes']}  flows={r['flows']}"
        )

    await io.write("Active sessions:\n" + "\n".join(lines))
