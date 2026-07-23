"""Demonstrates io.form() with plain dicts."""

from y5n.sdk import io


async def main():
    data = await io.form(
        fields=[
            {"key": "first_name", "title": "Vorname"},
            {"key": "last_name", "title": "Nachname", "required": True},
        ],
        title="Example Dialog",
    )
    await io.write(f"Result: {data}")
