from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from typing import TYPE_CHECKING, Any, Literal

from y5n.base.flow.dsl import Outcome, out, prompt, receive
from y5n.base.flow.policies import BasePolicy, ValidationError
from y5n.base.projection import Projection, ProjectionHeader, to_text
from y5n.base.projection.model.block import FieldsBlock, SectionBlock
from y5n.base.projection.model.field import Field

if TYPE_CHECKING:
    from y5n.base.nodes import Param

FieldsState = Literal["idle", "active", "done"]


class Form:

    def __init__(self, fields: list[Param] | None = None, *, title: str = ""):
        self._fields = fields
        self._title = title
        self._field_map: dict[str, Param] = {}
        if fields:
            self._field_map = {p.key: p for p in fields}
        self.data: dict[str, str] = {}
        self._titles: dict[str, str] = {}
        self._error: str | None = None

    def _render(self, active_key: str = "") -> Projection:
        if self._fields is not None:
            return self._render_structured(active_key)
        return self._render_text(active_key)

    def _render_text(self, title: str = "") -> Projection:
        lines = []
        for key, value in self.data.items():
            label = self._titles.get(key, key.replace("_", " ").title())
            lines.append(f"{label}: {value}")
        if title:
            lines.append(title)
        if self._error:
            lines.append(f"  ! {self._error}")
        return to_text("\n".join(lines))

    def _render_structured(self, active_key: str) -> Projection:
        fb_fields: list[Field] = []
        for param in self._fields:
            if param.key == active_key:
                state: FieldsState = "active"
            elif param.key in self.data:
                state = "done"
            else:
                state = "idle"

            fb_fields.append(Field(
                policy=str(param.policy) if param.policy else "string",
                title=self._titles.get(param.key, param.title or param.key.title()),
                required=param.required,
                name=param.key,
                value=self.data.get(param.key),
            ))

        fields_block = FieldsBlock(
            id=f"fld.{uuid.uuid4().hex[:8]}",
            name=self._title,
            fields=fb_fields,
            state="active",
        )
        header = ProjectionHeader(title=self._title, role="input")
        return Projection.create(
            header=header,
            blocks=[SectionBlock(blocks=[fields_block])],
        )

    async def ask(
        self,
        key: str,
        title: str,
        policy: BasePolicy | None = None,
    ) -> AsyncGenerator[Outcome, Any]:

        while True:

            yield prompt(self._render(key))
            event = yield receive()

            try:

                if policy:
                    result = policy.validate(event.payload)
                else:
                    result = event.payload

                value: str = result if result is not None else ""
                self.data[key] = value
                self._titles[key] = title.rstrip(": ")
                self._error = None
                yield out(self._render())
                break

            except ValidationError as e:
                self._error = e.args[0]
                yield prompt(self._render(key))
