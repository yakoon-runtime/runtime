"""Demonstrates io.form() with initial values, focus, and required fields."""

from y5n.sdk import io
from y5n.sdk.models import Field


async def main():
    data = await io.form(
        fields=[
            Field(key="first_name", title="Vorname"),
            Field(key="last_name", title="Nachname", required=True),
            Field(key="age", title="Alter"),
            Field(key="street", title="Straße", required=True),
        ],
        title="Example Form",
        intro="A quick test...",
        initial={"first_name": "stefan"},
        focus="last_name",
    )
    await io.write(f"Result: {data}")
