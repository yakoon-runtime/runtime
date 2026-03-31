from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import Any, cast
from uuid import uuid4

import yaml

from yakoon.base.projection.model import (
    Block,
    ErrorKind,
    Field,
    FieldsBlock,
    FieldsState,
    FieldType,
    Inline,
    InlineCode,
    InlineLink,
    InlineText,
    InputMode,
    KvBlock,
    KvItemBlock,
    ListBlock,
    ListItemBlock,
    Projection,
    ProjectionHeader,
    Role,
    RuleBlock,
    RuleStyle,
    SelectOption,
    SpacerBlock,
    TableBlock,
    TextBlock,
)

RULE_STYLES = ("subtle", "normal", "strong")
BlockParser = Callable[[str | None, dict[str, Any]], Block]


class ViewSpecError(Exception):
    pass


class ViewSpecParseError(ViewSpecError):
    pass


class ViewSpecValidationError(ViewSpecError):
    pass


class YamlProjectionParser:
    """
    Parse a single projection file.

    Root:
      kind: projection
      projection: { role?, title?, subtitle?, error_kind?, blocks }

    One file == one projection. No sections. No bundles.

    Interactive input is represented as a normal block:
      - type: fields
    """

    def __init__(self) -> None:
        self._block_parsers: dict[str, BlockParser] = {
            "text": self._parse_text_block,
            "list_item": self._parse_list_item_block,
            "list": self._parse_list_block,
            "kv": self._parse_kv_block,
            "table": self._parse_table_block,
            "fields": self._parse_fields_block,
            "rule": self._parse_rule_block,
            "spacer": self._parse_spacer_block,
        }

    def parse_spec(self, yaml_text: str) -> Projection:
        raw = self._load_yaml_mapping(yaml_text)

        kind = raw.get("kind")
        if kind != "projection":
            raise ViewSpecValidationError(
                f"Unknown root kind: {kind!r} (expected 'projection')"
            )

        projection = raw.get("projection")
        if not isinstance(projection, dict):
            raise ViewSpecValidationError("projection must be a mapping")

        return self._parse_projection_body(projection)

    def _load_yaml_mapping(self, yaml_text: str) -> dict[str, Any]:
        try:
            raw = yaml.safe_load(yaml_text)
        except Exception as e:  # noqa: BLE001
            raise ViewSpecParseError(f"Invalid YAML: {e}") from e

        if not isinstance(raw, dict):
            raise ViewSpecParseError("Root must be a mapping")
        return raw

    def _parse_projection_body(self, projection: dict[str, Any]) -> Projection:
        if "fields" in projection:
            raise ViewSpecValidationError(
                "projection.fields is no longer supported; use a block with type='fields' inside projection.blocks"
            )
        if "input_mode" in projection:
            raise ViewSpecValidationError(
                "projection.input_mode is no longer supported; use input_mode on a 'fields' block"
            )

        projection_id = projection.get("id")
        if projection_id is not None and not isinstance(projection_id, str):
            raise ViewSpecValidationError("id must be a string or null")
        if projection_id is None:
            projection_id = f"prj.{uuid4().hex}"

        role = projection.get("role", "info")
        if role not in ("info", "success", "warning", "error", "help"):
            raise ViewSpecValidationError(f"Invalid role: {role!r}")

        title = projection.get("title")
        if title is not None and not isinstance(title, str):
            raise ViewSpecValidationError("title must be a string or null")

        subtitle = projection.get("subtitle")
        if subtitle is not None and not isinstance(subtitle, str):
            raise ViewSpecValidationError("subtitle must be a string or null")

        error_kind = projection.get("error_kind")
        if error_kind is not None and error_kind not in ("validation", "system"):
            raise ViewSpecValidationError(
                "error_kind must be 'validation', 'system', or null"
            )

        blocks_raw = projection.get("blocks")
        if not isinstance(blocks_raw, list) or not blocks_raw:
            raise ViewSpecValidationError("projection.blocks must be a non-empty list")

        blocks = [self._parse_block(b) for b in blocks_raw]
        blocks = self._ensure_block_ids(projection_id, blocks)

        header = ProjectionHeader(
            role=cast(Role, role),
            title=title,
            subtitle=subtitle,
            error_kind=cast(ErrorKind | None, error_kind),
            meta=None,
        )

        return Projection(
            kind="projection",
            id=projection_id,
            header=header,
            blocks=blocks,
        )

    def _ensure_block_ids(self, projection_id: str, blocks: list[Block]) -> list[Block]:

        def assign(block: Block, path: str) -> Block:
            bid = block.id or path
            block = replace(block, id=bid)

            children = block.children()
            if not children:
                return block

            new_children = [
                assign(child, f"{bid}.{i}") for i, child in enumerate(children)
            ]

            if hasattr(block, "blocks"):
                block = replace(block, blocks=new_children)

            elif hasattr(block, "items"):
                block = replace(block, items=new_children)

            return block

        return [assign(b, f"{projection_id}.{i}") for i, b in enumerate(blocks)]

    def _parse_fields_block(
        self, block_id: str | None, b: dict[str, Any]
    ) -> FieldsBlock:
        fields_raw = b.get("fields")
        if not isinstance(fields_raw, list) or not fields_raw:
            raise ViewSpecValidationError("FieldsBlock.fields must be a non-empty list")

        input_mode = b.get("input_mode", "prompt")
        if input_mode is None:
            input_mode = "prompt"
        if not isinstance(input_mode, str) or input_mode not in ("prompt", "form"):
            raise ViewSpecValidationError(
                "FieldsBlock.input_mode must be 'prompt' or 'form'"
            )

        title = b.get("title")
        if title is not None and not isinstance(title, str):
            raise ViewSpecValidationError("FieldsBlock.title must be a string or null")

        step_key = b.get("step_key")
        if step_key is not None and not isinstance(step_key, str):
            raise ViewSpecValidationError(
                "FieldsBlock.step_key must be a string or null"
            )

        batch_id = b.get("batch_id")
        if batch_id is not None and not isinstance(batch_id, str):
            raise ViewSpecValidationError(
                "FieldsBlock.batch_id must be a string or null"
            )

        state = b.get("state", "idle")
        if not isinstance(state, str) or state not in ("idle", "active", "done"):
            raise ViewSpecValidationError(
                "FieldsBlock.state must be 'idle', 'active', or 'done'"
            )

        aliases: dict[str, str] = {}
        order: list[str] = []
        seen_vars: set[str] = set()
        parsed_fields: list[Field] = []

        for i, item in enumerate(fields_raw):
            if not isinstance(item, dict):
                raise ViewSpecValidationError(f"fields[{i}] must be a mapping")

            var = item.get("var")
            if not isinstance(var, str) or not var:
                raise ViewSpecValidationError(
                    f"fields[{i}].var must be a non-empty string"
                )
            if var in seen_vars:
                raise ViewSpecValidationError(f"Duplicate var {var!r} in fields")

            key = item.get("key")
            if key is not None and (not isinstance(key, str) or not key):
                raise ViewSpecValidationError(
                    f"fields[{i}].key must be a non-empty string or null"
                )

            if key:
                if key in aliases:
                    raise ViewSpecValidationError(
                        f"Duplicate key alias {key!r} in fields"
                    )
                if key == var:
                    raise ViewSpecValidationError(
                        f"Alias {key!r} collides with its own var"
                    )
                aliases[key] = var

            parsed_fields.append(self._parse_field_def(field_id=var, fd=item))
            order.append(var)
            seen_vars.add(var)

        meta: dict[str, Any] = {"aliases": aliases, "order": order}

        return FieldsBlock(
            type="fields",
            id=block_id,
            fields=parsed_fields,
            input_mode=cast(InputMode, input_mode),
            title=title,
            step_key=step_key,
            batch_id=batch_id,
            state=cast(FieldsState, state),
            meta=meta or None,
        )

    def _parse_field_def(self, *, field_id: str, fd: dict[str, Any]) -> Field:
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

        type_raw = fd.get("type")
        field_type: FieldType | None = None
        if type_raw is not None:
            if not isinstance(type_raw, str):
                raise ViewSpecValidationError(
                    f"fields[{field_id}].type must be a string or null"
                )
            try:
                field_type = FieldType(type_raw)
            except ValueError as e:
                raise ViewSpecValidationError(
                    f"fields[{field_id}].type has invalid value {type_raw!r}"
                ) from e

        options_raw = fd.get("options")
        options: list[SelectOption] | None = None
        if options_raw is not None:
            if field_type != FieldType.SELECT:
                raise ViewSpecValidationError(
                    f"fields[{field_id}].options is only allowed for select fields"
                )
            if not isinstance(options_raw, list):
                raise ViewSpecValidationError(
                    f"fields[{field_id}].options must be a list"
                )

            parsed_options: list[SelectOption] = []
            for j, opt in enumerate(options_raw):
                if not isinstance(opt, dict):
                    raise ViewSpecValidationError(
                        f"fields[{field_id}].options[{j}] must be a mapping"
                    )
                value = opt.get("value")
                label = opt.get("label")
                if not isinstance(value, str) or not isinstance(label, str):
                    raise ViewSpecValidationError(
                        f"fields[{field_id}].options[{j}] must define string value and label"
                    )
                parsed_options.append(SelectOption(value=value, label=label))
            options = parsed_options

        return Field(
            policy=policy,
            title=title_,
            required=required,
            var=var,
            hint=hint,
            default=default,
            pattern=pattern,
            ui=ui or None,
            type=field_type,
            options=options,
        )

    def _parse_block(self, b: Any) -> Block:
        if not isinstance(b, dict):
            raise ViewSpecValidationError("Each block must be a mapping")

        t = b.get("type")
        if not isinstance(t, str) or not t:
            raise ViewSpecValidationError("Each block must define a non-empty 'type'")

        bid = self._validate_block_id(b.get("id"))

        handler = self._block_parsers.get(t)
        if handler is None:
            raise ViewSpecValidationError(f"Unknown block type: {t!r}")

        return handler(bid, b)

    def _parse_text_block(self, bid: str | None, b: dict[str, Any]) -> TextBlock:
        return TextBlock(
            type="text",
            id=bid,
            text=self._parse_text_content(b.get("text", "")),
        )

    def _parse_list_item_block(
        self, bid: str | None, b: dict[str, Any]
    ) -> ListItemBlock:
        head = self._parse_text_content(b.get("head", ""))

        blocks_raw = b.get("blocks")
        if blocks_raw is None:
            return ListItemBlock(type="list_item", id=bid, head=head, blocks=None)

        if not isinstance(blocks_raw, list):
            raise ViewSpecValidationError("ListItemBlock.blocks must be a list or null")

        nested = [self._parse_block(x) for x in blocks_raw]
        return ListItemBlock(type="list_item", id=bid, head=head, blocks=nested)

    def _parse_list_block(self, bid: str | None, b: dict[str, Any]) -> ListBlock:
        items_raw = b.get("items", [])
        if not isinstance(items_raw, list):
            raise ViewSpecValidationError("ListBlock.items must be a list")

        return ListBlock(
            type="list",
            id=bid,
            items=[self._parse_list_item(x) for x in items_raw],
        )

    def _parse_kv_block(self, bid: str | None, b: dict[str, Any]) -> KvBlock:
        items_raw = b.get("items", [])
        if not isinstance(items_raw, list):
            raise ViewSpecValidationError("KvBlock.items must be a list")

        parsed_items: list[KvItemBlock] = []
        for entry in items_raw:
            if not isinstance(entry, list) or len(entry) != 2:
                raise ViewSpecValidationError(
                    "Each kv item must be a [key, value] list"
                )

            key, value = entry
            parsed_items.append(
                KvItemBlock(
                    key=str(key),
                    value=(
                        str(value)
                        if isinstance(value, (str, int, float, bool))
                        else value
                    ),
                    id=None,
                )
            )

        return KvBlock(type="kv", id=bid, items=parsed_items)

    def _parse_table_block(self, bid: str | None, b: dict[str, Any]) -> TableBlock:
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

    def _parse_rule_block(self, bid: str | None, b: dict[str, Any]) -> RuleBlock:
        return RuleBlock(
            type="rule",
            id=bid,
            style=self._parse_rule_style(b.get("style")),
        )

    def _parse_spacer_block(self, bid: str | None, b: dict[str, Any]) -> SpacerBlock:
        size = b.get("size", 1)
        if not isinstance(size, int) or size < 0:
            raise ViewSpecValidationError(
                "SpacerBlock.size must be a non-negative integer"
            )
        return SpacerBlock(type="spacer", id=bid, size=size)

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
            return "normal"
        if not isinstance(value, str):
            raise ViewSpecValidationError("RuleBlock.style must be a string")
        if value not in RULE_STYLES:
            raise ViewSpecValidationError(
                f"Invalid rule style: {value!r}. Expected one of: {RULE_STYLES}"
            )
        return cast(RuleStyle, value)

    def _validate_block_id(self, bid: Any) -> str | None:
        if bid is None:
            return None
        if not isinstance(bid, str) or not bid:
            raise ViewSpecValidationError("Block.id must be a non-empty string or null")
        return bid

    def _parse_list_item(self, node: Any) -> ListItemBlock:
        if isinstance(node, str):
            return ListItemBlock(type="list_item", head=node, blocks=None, id=None)

        if isinstance(node, list):
            head = [self._parse_inline(x) for x in node]
            return ListItemBlock(type="list_item", head=head, blocks=None, id=None)

        if not isinstance(node, dict):
            raise ViewSpecValidationError(
                "List item must be string, inline-list, or mapping"
            )

        iid = self._validate_block_id(node.get("id"))
        head = self._parse_text_content(node.get("head", ""))

        blocks_raw = node.get("blocks")
        if blocks_raw is None:
            return ListItemBlock(type="list_item", head=head, blocks=None, id=iid)

        if not isinstance(blocks_raw, list):
            raise ViewSpecValidationError("ListItemBlock.blocks must be a list or null")

        nested = [self._parse_block(b) for b in blocks_raw]
        return ListItemBlock(type="list_item", head=head, blocks=nested, id=iid)
