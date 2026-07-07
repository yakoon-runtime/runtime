from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator, Mapping
from typing import Any

from y5n.base.flow.dsl import Outcome, out, prompt, receive
from y5n.base.flow.policies import BasePolicy, ValidationError
from y5n.base.nodes import Param
from y5n.base.projection import Projection, ProjectionHeader
from y5n.base.projection.model.block import FieldsBlock, SectionBlock
from y5n.base.projection.model.field import Field, FieldsState


class Form:
    """Interactive form for collecting structured user input.

    A form consists of one or more fields that are validated individually.
    After each input the form is re-rendered, allowing clients to display
    progress and validation errors.

    Fields may be registered upfront or added dynamically while the dialog
    is running.

    Modes

        Form
            All fields are known before execution.

            async for step in form.run():
                yield step

        Dialog
            Fields are added incrementally.

            yield form.ask("first_name", "First name")
            yield form.ask("last_name", "Last name")

    Initial values

        `initial` provides pre-filled values (for example when editing an
        existing entity). Existing values are displayed and may be changed.
        The first field without a value becomes the active field.
    """

    def __init__(
        self,
        fields: list[Param] | None = None,
        *,
        title: str = "",
        initial: dict[str, str] | None = None,
    ):
        self._fields: list[Param] = list(fields) if fields is not None else []
        self._title = title
        self._field_map: dict[str, Param] = {p.key: p for p in self._fields}
        self.data: dict[str, str] = dict(initial or {})
        self._error: str | None = None

    # --------------------------------------------------------
    # Dialog
    # --------------------------------------------------------

    async def run(self) -> AsyncGenerator[AsyncGenerator[Outcome, Any], None]:
        """Yield a sub-generator for each registered field.

        The caller forwards each sub-generator to the engine:

            async for step in form.run():
                yield step
        """
        for param in self._fields:
            yield self.ask(
                key=param.key,
                title=param.title or param.key.title(),
                policy=param.policy,
            )

    @property
    def values(self) -> Mapping[str, str]:
        return dict(self.data)

    # --------------------------------------------------------
    # Rendering
    # --------------------------------------------------------

    def _render(self, active_key: str = "") -> Projection:
        return self._render_structured(active_key)

    def _render_structured(self, active_key: str) -> Projection:
        fb_fields: list[Field] = []

        for param in self._fields:
            if param.key == active_key:
                state: FieldsState = "active"
            elif param.key in self.data:
                state = "done"
            else:
                state = "idle"

            fb_fields.append(
                Field(
                    policy=str(param.policy) if param.policy else "string",
                    title=param.title or param.key.title(),
                    required=param.required,
                    name=param.key,
                    value=self.data.get(param.key),
                    state=state,
                    error=(
                        self._error if param.key == active_key and self._error else None
                    ),
                )
            )

        fields_block = FieldsBlock(
            id=f"fld.{uuid.uuid4().hex[:8]}",
            name=self._title,
            fields=fb_fields,
            state="active",
        )
        header = ProjectionHeader(title=self._title, role="info")
        return Projection.create(
            header=header,
            blocks=[SectionBlock(blocks=[fields_block])],
        )

    # --------------------------------------------------------
    # Field lifecycle
    # --------------------------------------------------------

    async def ask(
        self,
        key: str,
        title: str,
        policy: BasePolicy | None = None,
    ) -> AsyncGenerator[Outcome, Any]:

        if key not in self._field_map:
            param = Param(key=key, title=title.rstrip(": "), policy=policy)
            self._fields.append(param)
            self._field_map[key] = param

        while True:

            yield prompt(self._render(key))
            event = yield receive()

            try:

                if policy:
                    result = policy.validate(event.payload)
                else:
                    result = event.payload

                value: str = result if result is not None else ""
                if not value:
                    value = self.data.get(key, "")
                self.data[key] = value
                self._error = None
                yield out(self._render())
                break

            except ValidationError as e:
                self._error = e.args[0]
                yield prompt(self._render(key))
