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

from .dialog import Dialog
from .form_action import FormAction


class Form:
    """Interactive form for collecting structured user input.

    A form consists of one or more fields that are validated individually.
    After each input the form is re-rendered, allowing clients to display
    progress and validation errors.

    Fields may be registered upfront or added on the fly.

    Two modes of operation:

        Form (all fields upfront):
            async for step in form.run():
                yield step

        Dialog (field-by-field):
            yield form.ask("first_name", "First name")
            yield form.ask("last_name", "Last name")

    Initial values

        `initial` provides pre-filled values. Existing values are
        displayed as "done" and are skipped by run().

    Focus

        `intro` is an optional paragraph shown between the title and the
    fields to give context or instructions.

            Form(
                title="Kontakt",
                intro="Bitte geben Sie die Stammdaten des neuen Kontakts ein.",
            )

    `focus` sets the field where the cursor starts.

            Form(
                fields=[Param("username", ...), Param("password", ...)],
                initial={"username": "stefan"},
                focus="password",
            )

    Keyboard shortcuts (ShellInput)

        Enter      Accept the current field and advance.
        Ctrl+Up    Move to the previous field.
        Ctrl+Down  Move to the next field.
        Ctrl+N     Jump to the next empty required field,
                   or complete the form when all are filled.
        Esc        Suspend the foreground flow (sends /jobs/bg).
        Ctrl+X     Cancel the current flow (sends /jobs/stop --current).
    """

    def __init__(
        self,
        fields: list[Param] | None = None,
        *,
        title: str = "",
        intro: str = "",
        initial: dict[str, str] | None = None,
        focus: str | None = None,
    ):
        self._dialog = Dialog(fields or [], focus_key=focus)
        self._fields: list[Param] = self._dialog.fields  # reference
        self._title = title
        self._intro = intro
        self._field_map: dict[str, Param] = {p.key: p for p in self._fields}
        self.data: dict[str, str] = dict(initial or {})
        self._error: str | None = None
        self._navigated = False

    # --------------------------------------------------------
    # Dialog
    # --------------------------------------------------------

    async def run(self) -> AsyncGenerator[AsyncGenerator[Outcome, Any], None]:
        """Yield a sub-generator for each field until the dialog completes.

        The caller forwards each sub-generator to the engine:

            async for step in form.run():
                yield step
        """
        while not self._dialog.completed:
            param = self._dialog.current
            if param is None:
                break
            yield self._ask_field(
                key=param.key,
                title=param.title or param.key.title(),
                policy=param.policy,
            )
            if self._navigated:
                self._navigated = False
                continue
            self._advance()

    @property
    def values(self) -> Mapping[str, str]:
        return dict(self.data)

    # --------------------------------------------------------
    # Actions
    # --------------------------------------------------------

    def apply(self, action: FormAction) -> None:
        """Apply a navigation action to the form cursor."""
        match action.action:
            case "next":
                if self._dialog.has_next:
                    self._dialog.next()
            case "previous":
                self._dialog.previous()
            case "focus":
                if action.target:
                    self._dialog.focus(action.target)
            case "submit":
                self._submit()

    def _advance(self) -> None:
        self._dialog.next()
        if self._dialog.completed:
            missing = self._first_missing_required()
            if missing:
                self._dialog.focus(missing.key)
                self._navigated = True

    def _submit(self) -> None:
        missing = self._first_missing_required()
        if missing:
            self._dialog.focus(missing.key)
            self._navigated = True
        else:
            self._dialog.next()

    def _first_missing_required(self) -> Param | None:
        for p in self._fields:
            if p.required and not self._is_filled(p.key):
                return p
        return None

    def _is_filled(self, key: str) -> bool:
        return self.data.get(key) not in (None, "")

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
            elif self._is_filled(param.key):
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
            intro=self._intro or None,
            state="active",
        )
        header = ProjectionHeader(title=self._title, role="info")
        return Projection.create(
            header=header,
            blocks=[SectionBlock(blocks=[fields_block])],
        )

    # --------------------------------------------------------
    # Field lifecycle (used by both run() and standalone ask())
    # --------------------------------------------------------

    def ask(
        self,
        key: str,
        title: str,
        policy: BasePolicy | None = None,
    ) -> AsyncGenerator[Outcome, Any]:
        """Register a field on the fly and return its input sub-generator.

        Used in dialog mode (field-by-field):

            yield form.ask("first_name", "First name")
        """
        if key not in self._field_map:
            param = Param(key=key, title=title.rstrip(": "), policy=policy)
            self._fields.append(param)
            self._field_map[key] = param

        return self._ask_field(key, title, policy)

    async def _ask_field(
        self,
        key: str,
        title: str,
        policy: BasePolicy | None = None,
    ) -> AsyncGenerator[Outcome, Any]:
        """Core lifecycle for a single field: prompt, receive, validate.

        If the incoming event is a FormAction, it is applied to the dialog
        and the sub-generator returns — run() re-evaluates the cursor.
        """

        while True:

            yield prompt(self._render(key))
            event = yield receive()

            if isinstance(event.payload, FormAction):
                self.apply(event.payload)
                self._navigated = True
                return

            try:

                if policy:
                    result = policy.validate(event.payload)
                else:
                    result = event.payload

                value = str(result) if result is not None else ""
                if not value:
                    value = self.data.get(key, "")

                param = self._field_map.get(key)
                if param and param.required and not value:
                    yield prompt(self._render(key))
                    continue

                self.data[key] = value
                self._error = None
                yield out(self._render())
                break

            except ValidationError as e:
                self._error = e.args[0]
                yield prompt(self._render(key))
