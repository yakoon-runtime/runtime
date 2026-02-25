from __future__ import annotations

from typing import Any, Literal, cast

import yaml

from yakoon.base.models.message import (
    Block,
    Inline,
    InlineCode,
    InlineLink,
    InlineText,
    KvBlock,
    ListBlock,
    ListItem,
    MessageSpec,
    RuleBlock,
    SpacerBlock,
    TableBlock,
    TextBlock,
)
from yakoon.base.models.view import ViewFieldDef, ViewFormDef, ViewSpec


class ViewSpecError(Exception): ...


class ViewSpecParseError(ViewSpecError): ...


class ViewSpecValidationError(ViewSpecError): ...


Role = Literal["info", "success", "warning", "error", "help"]
RuleStyle = Literal["subtle", "normal", "strong"]
RULE_STYLES = {"subtle", "normal", "strong"}


class ViewSpecService:
    """
    Parse a single state file.

    Root:
      kind: state
      state: { role?, title?, blocks?, fields? }

    One file == one state. No sections. No bundles.
    """

    def parse_spec(self, yaml_text: str) -> ViewSpec:
        raw = self._load_yaml_mapping(yaml_text)

        kind = raw.get("kind")
        if kind != "state":
            raise ViewSpecValidationError(
                f"Unknown root kind: {kind!r} (expected 'state')"
            )

        state = raw.get("state")
        if not isinstance(state, dict):
            raise ViewSpecValidationError("state must be a mapping")

        message, input_def = self._parse_state_body(state)

        if message is None and input_def is None:
            raise ViewSpecValidationError("state must define blocks and/or fields")

        return ViewSpec(
            kind="view",
            mode="replace",
            id=None,  # optional: later derive from command_key/state in renderer
            message=message,
            input=input_def,
            meta=None,
        )

    # -----------------------
    # YAML loading
    # -----------------------

    def _load_yaml_mapping(self, yaml_text: str) -> dict[str, Any]:
        try:
            raw = yaml.safe_load(yaml_text)
        except Exception as e:  # noqa: BLE001
            raise ViewSpecParseError(f"Invalid YAML: {e}") from e

        if not isinstance(raw, dict):
            raise ViewSpecParseError("Root must be a mapping")
        return raw

    # -----------------------
    # state parsing
    # -----------------------

    def _parse_state_body(
        self, state: dict[str, Any]
    ) -> tuple[MessageSpec | None, ViewFormDef | None]:
        # Output (blocks)
        role = state.get("role", "info")
        if role is not None and role not in (
            "info",
            "success",
            "warning",
            "error",
            "help",
        ):
            raise ViewSpecValidationError(f"Invalid role: {role!r}")

        title = state.get("title")
        if title is not None and not isinstance(title, str):
            raise ViewSpecValidationError("title must be a string or null")

        blocks_raw = state.get("blocks")
        message: MessageSpec | None = None
        if blocks_raw is not None:
            if not isinstance(blocks_raw, list):
                raise ViewSpecValidationError("blocks must be a list or null")
            blocks = [self._parse_block(b) for b in blocks_raw]
            message = MessageSpec(
                kind="message",
                role=cast(Role, role),
                title=title,
                blocks=blocks,
                meta=None,
            )

        # Input (fields)
        fields_raw = state.get("fields")
        input_def: ViewFormDef | None = None
        if fields_raw is not None:
            if not isinstance(fields_raw, list) or not fields_raw:
                raise ViewSpecValidationError("fields must be a non-empty list or null")

            input_mode = state.get("input_mode", "prompt")
            if input_mode is None:
                input_mode = "prompt"
            if not isinstance(input_mode, str) or input_mode not in ("prompt", "form"):
                raise ViewSpecValidationError("input_mode must be 'prompt' or 'form'")

            input_def = self._parse_fields(
                fields_raw, title=title, input_mode=input_mode
            )

        return message, input_def

    def _parse_fields(
        self, fields_raw: list[Any], *, title: str | None, input_mode: str
    ) -> ViewFormDef:
        # Minimal, deterministic form_id for now.
        # Later you can pass base_id from renderer: f"{command_key}.{state}"
        form_id = "form"

        aliases: dict[str, str] = {}
        order: list[str] = []
        fields: dict[str, ViewFieldDef] = {}

        for i, item in enumerate(fields_raw):
            if not isinstance(item, dict):
                raise ViewSpecValidationError(f"fields[{i}] must be a mapping")

            var = item.get("var")
            if not isinstance(var, str) or not var:
                raise ViewSpecValidationError(
                    f"fields[{i}].var must be a non-empty string"
                )
            if var in fields:
                raise ViewSpecValidationError(f"Duplicate var {var!r} in fields")

            key = item.get("key")
            if key is not None and (not isinstance(key, str) or not key):
                raise ViewSpecValidationError(
                    f"fields[{i}].key must be a non-empty string or null"
                )

            fd = self._parse_field_def(field_id=var, fd=item)
            fields[var] = fd
            order.append(var)

            if key:
                if key in aliases:
                    raise ViewSpecValidationError(
                        f"Duplicate key alias {key!r} in fields"
                    )
                if key == var or key in fields:
                    raise ViewSpecValidationError(
                        f"Alias {key!r} collides with a var in fields"
                    )
                if var in aliases:
                    raise ViewSpecValidationError(
                        f"var {var!r} collides with an alias key in fields"
                    )
                aliases[key] = var

        meta: dict[str, Any] = {"aliases": aliases, "order": order}

        return ViewFormDef(
            kind="form",
            form_id=form_id,
            fields=fields,
            input_mode=cast(Literal["prompt", "form"], input_mode),
            title=title,
            meta=meta,
        )

    def _parse_field_def(self, *, field_id: str, fd: dict[str, Any]) -> ViewFieldDef:
        policy = fd.get("policy")
        if not isinstance(policy, str) or not policy:
            raise ViewSpecValidationError(
                f"fields[{field_id}].policy must be a non-empty string"
            )

        title_ = fd.get("title")
        if title_ is not None and not isinstance(title_, str):
            raise ViewSpecValidationError(
                f"fields[{field_id}].title must be a string or null"
            )

        required = fd.get("required", False)
        if isinstance(required, str):
            lowered = required.strip().lower()
            if lowered in {"true", "yes", "1"}:
                required = True
            elif lowered in {"false", "no", "0"}:
                required = False
        if not isinstance(required, bool):
            raise ViewSpecValidationError(
                f"fields[{field_id}].required must be a boolean"
            )

        var = fd.get("var")
        if not isinstance(var, str) or not var:
            raise ViewSpecValidationError(
                f"fields[{field_id}].var must be a non-empty string"
            )

        hint = fd.get("hint", "")
        default = fd.get("default", "")
        pattern = fd.get("pattern", "")
        if (
            not isinstance(hint, str)
            or not isinstance(default, str)
            or not isinstance(pattern, str)
        ):
            raise ViewSpecValidationError(
                f"fields[{field_id}] hint/default/pattern must be strings"
            )

        ui_raw = fd.get("ui")
        if ui_raw is not None and not isinstance(ui_raw, dict):
            raise ViewSpecValidationError(
                f"fields[{field_id}].ui must be a mapping or null"
            )
        ui = dict(ui_raw or {})

        if policy in {"system:masked"} or policy.endswith(":masked"):
            ui.setdefault("secret", True)

        return ViewFieldDef(
            policy=policy,
            title=title_,
            required=required,
            var=var,
            hint=hint,
            default=default,
            pattern=pattern,
            ui=ui or None,
        )

    # -----------------------
    # blocks / inline (reuse)
    # -----------------------

    def _parse_text_content(self, value: Any) -> str | list[Inline]:
        if isinstance(value, str):
            return value
        if isinstance(value, list):
            return [self._parse_inline(x) for x in value]
        raise ViewSpecValidationError("text must be a string or a list of inline nodes")

    def _parse_inline(self, node: Any) -> Inline:
        if not isinstance(node, dict):
            raise ViewSpecValidationError("Inline node must be a mapping")

        t = node.get("type")
        if t == "text":
            text = node.get("text", "")
            if not isinstance(text, str):
                raise ViewSpecValidationError("InlineText.text must be a string")
            return InlineText(type="text", text=text)

        if t == "code":
            code = node.get("code", "")
            if not isinstance(code, str):
                raise ViewSpecValidationError("InlineCode.code must be a string")
            return InlineCode(type="code", code=code)

        if t == "link":
            text = node.get("text", "")
            href = node.get("href", "")
            if not isinstance(text, str) or not isinstance(href, str):
                raise ViewSpecValidationError("InlineLink.text/href must be strings")
            return InlineLink(type="link", text=text, href=href)

        raise ViewSpecValidationError(f"Unknown inline type: {t!r}")

    def _parse_rule_style(self, value: Any) -> RuleStyle:
        if value is None:
            value = "normal"
        if not isinstance(value, str):
            raise ViewSpecValidationError("RuleBlock.style must be a string")
        if value not in RULE_STYLES:
            raise ViewSpecValidationError(
                f"Invalid rule style: {value!r}. Expected one of: {sorted(RULE_STYLES)}"
            )
        return cast(RuleStyle, value)

    def _parse_list_item(self, node: Any) -> ListItem:
        if isinstance(node, str):
            return ListItem(head=node, blocks=None)

        if isinstance(node, list):
            head = [self._parse_inline(x) for x in node]
            return ListItem(head=head, blocks=None)

        if not isinstance(node, dict):
            raise ViewSpecValidationError(
                "List item must be string, inline-list, or mapping"
            )

        head = self._parse_text_content(node.get("head", ""))

        blocks_raw = node.get("blocks")
        if blocks_raw is None:
            return ListItem(head=head, blocks=None)

        if not isinstance(blocks_raw, list):
            raise ViewSpecValidationError("ListItem.blocks must be a list or null")

        nested = [self._parse_block(b) for b in blocks_raw]
        return ListItem(head=head, blocks=nested)

    def _parse_block(self, b: Any) -> Block:
        if not isinstance(b, dict):
            raise ViewSpecValidationError("Each block must be a mapping")

        t = b.get("type")
        bid = b.get("id")

        if t == "text":
            return TextBlock(
                type="text", id=bid, text=self._parse_text_content(b.get("text", ""))
            )

        if t == "list":
            items_raw = b.get("items", [])
            if not isinstance(items_raw, list):
                raise ViewSpecValidationError("ListBlock.items must be a list")
            return ListBlock(
                type="list", id=bid, items=[self._parse_list_item(x) for x in items_raw]
            )

        if t == "table":
            headers = b.get("headers")
            if headers is not None:
                if not isinstance(headers, list) or not all(
                    isinstance(x, str) for x in headers
                ):
                    raise ViewSpecValidationError(
                        "TableBlock.headers must be list[str] or null"
                    )

            rows = b.get("rows", [])
            if not isinstance(rows, list):
                raise ViewSpecValidationError("TableBlock.rows must be a list")

            parsed_rows: list[list[str]] = []
            for r in rows:
                if not isinstance(r, list) or not all(isinstance(x, str) for x in r):
                    raise ViewSpecValidationError("Each table row must be list[str]")
                parsed_rows.append(r)

            width = (
                len(headers)
                if headers is not None
                else (len(parsed_rows[0]) if parsed_rows else 0)
            )
            if headers is not None and any(len(r) != len(headers) for r in parsed_rows):
                raise ViewSpecValidationError("All rows must match headers length")
            if headers is None and any(len(r) != width for r in parsed_rows):
                raise ViewSpecValidationError("All rows must have equal length")

            return TableBlock(type="table", id=bid, headers=headers, rows=parsed_rows)

        if t == "kv":
            items = b.get("items", [])
            if not isinstance(items, list):
                raise ViewSpecValidationError("KvBlock.items must be a list")
            pairs: list[tuple[str, Any]] = []
            for entry in items:
                if not isinstance(entry, list) or len(entry) != 2:
                    raise ViewSpecValidationError(
                        "Each kv item must be a [key, value] list"
                    )
                k, v = entry
                pairs.append((str(k), v))
            return KvBlock(type="kv", id=bid, items=pairs)

        if t == "rule":
            return RuleBlock(
                type="rule", id=bid, style=self._parse_rule_style(b.get("style"))
            )

        if t == "spacer":
            size = b.get("size", 1)
            if not isinstance(size, int) or size < 0:
                raise ViewSpecValidationError(
                    "SpacerBlock.size must be a non-negative integer"
                )
            return SpacerBlock(type="spacer", id=bid, size=size)

        raise ViewSpecValidationError(f"Unknown block type: {t!r}")
