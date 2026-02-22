# yakoon/platform/services/view.py
from __future__ import annotations

from typing import Any, Literal, cast

import yaml

from yakoon.base.models.message import (
    KvBlock,
    ListBlock,
    MessageSpec,
    RuleBlock,
    SpacerBlock,
    TextBlock,
)
from yakoon.base.models.view import (
    ViewFieldDef,
    ViewFormDef,
    ViewSpec,
)


class ViewSpecError(Exception): ...


class ViewSpecParseError(ViewSpecError): ...


class ViewSpecValidationError(ViewSpecError): ...


class ViewSpecService:
    """
    Parse and validate view payloads.

    Supports:
      - kind: view         (direct ViewSpec)
      - kind: command_view (bundle with views/inputs; needs section_key)
    """

    def parse_spec(
        self,
        yaml_text: str,
        *,
        section_key: str | None = None,
        base_id: str | None = None,
    ) -> ViewSpec:
        raw = self._load_yaml_mapping(yaml_text)

        kind = raw.get("kind")
        if kind == "view":
            return self._parse_view(raw)

        if kind == "command_view":
            if not section_key:
                raise ViewSpecValidationError("command_view requires section_key")
            return self._parse_command_view(
                raw, section_key=section_key, base_id=base_id
            )

        raise ViewSpecValidationError(f"Unknown root kind: {kind!r}")

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
    # command_view parsing
    # -----------------------

    def _parse_command_view(
        self, raw: dict[str, Any], *, section_key: str, base_id: str | None
    ) -> ViewSpec:
        mode = raw.get("mode", "replace")
        if mode not in ("replace", "append", "patch"):
            raise ViewSpecValidationError(f"Invalid mode: {mode!r}")

        views = raw.get("views", {})
        inputs = raw.get("inputs", {})

        if views is None:
            views = {}
        if inputs is None:
            inputs = {}

        if not isinstance(views, dict):
            raise ViewSpecValidationError("command_view.views must be a mapping")
        if not isinstance(inputs, dict):
            raise ViewSpecValidationError("command_view.inputs must be a mapping")

        # Prefer views namespace, then inputs namespace
        if section_key in views:
            msg_raw = views[section_key]
            if not isinstance(msg_raw, dict):
                raise ViewSpecValidationError(f"views.{section_key} must be a mapping")

            message = self._parse_message_spec_string_only(msg_raw)

            view_id = self._make_id(
                raw_id=raw.get("id"), base_id=base_id, section_key=section_key
            )

            return ViewSpec(
                kind="view",
                mode=mode,
                id=view_id,
                message=message,
                input=None,
                meta=None,
            )

        if section_key in inputs:
            node = inputs[section_key]
            if not isinstance(node, dict):
                raise ViewSpecValidationError(f"inputs.{section_key} must be a mapping")

            title = node.get("title")
            if title is not None and not isinstance(title, str):
                raise ViewSpecValidationError(
                    f"inputs.{section_key}.title must be a string or null"
                )

            # Enforce fields-only form (no shorthand)
            fields_raw = node.get("fields")
            if not isinstance(fields_raw, list) or not fields_raw:
                raise ViewSpecValidationError(
                    f"inputs.{section_key}.fields must be a non-empty list"
                )

            aliases: dict[str, str] = {}
            fields: dict[str, ViewFieldDef] = {}

            for i, item in enumerate(fields_raw):
                if not isinstance(item, dict):
                    raise ViewSpecValidationError(
                        f"inputs.{section_key}.fields[{i}] must be a mapping"
                    )

                var = item.get("var")
                if not isinstance(var, str) or not var:
                    raise ViewSpecValidationError(
                        f"inputs.{section_key}.fields[{i}].var must be a non-empty string"
                    )

                key = item.get("key")
                if key is not None and (not isinstance(key, str) or not key):
                    raise ViewSpecValidationError(
                        f"inputs.{section_key}.fields[{i}].key must be a non-empty string or null"
                    )

                if var in fields:
                    raise ViewSpecValidationError(
                        f"Duplicate var {var!r} in inputs.{section_key}"
                    )

                # FieldDef parsen (policy/title/required/...)
                fd = self._parse_field_def(
                    field_id=var, fd=item
                )  # field_id = var (primär)
                fields[var] = fd

                # Alias registrieren
                if key:

                    # 1) Duplicate alias
                    if key in aliases:
                        raise ViewSpecValidationError(
                            f"Duplicate key alias {key!r} in inputs.{section_key}"
                        )

                    # 2) Alias collides with any var (present or future) OR with current var
                    if key == var or key in fields:
                        raise ViewSpecValidationError(
                            f"Alias {key!r} collides with a var key in inputs.{section_key}"
                        )

                    # 3) Also prevent a var from colliding with an already-defined alias
                    if var in aliases:
                        raise ViewSpecValidationError(
                            f"var {var!r} collides with an alias key in inputs.{section_key}"
                        )

                    aliases[key] = var

            # meta (optional) + aliases/order
            meta_raw = node.get("meta")
            if meta_raw is not None and not isinstance(meta_raw, dict):
                raise ViewSpecValidationError(
                    f"inputs.{section_key}.meta must be a mapping or null"
                )

            meta: dict[str, Any] = dict(meta_raw or {})
            meta["aliases"] = aliases
            meta["order"] = list(fields.keys())

            form_id = self._make_form_id(
                raw_id=raw.get("id"), base_id=base_id, section_key=section_key
            )

            input_def = ViewFormDef(
                kind="form",
                form_id=form_id,
                fields=fields,
                title=title,
                meta=meta,
            )

            view_id = self._make_id(
                raw_id=raw.get("id"), base_id=base_id, section_key=section_key
            )

            return ViewSpec(
                kind="view",
                mode=mode,
                id=view_id,
                message=None,
                input=input_def,
                meta=None,
            )

        raise ViewSpecValidationError(
            f"Unknown section_key {section_key!r}. Expected one of views={sorted(views.keys())} or inputs={sorted(inputs.keys())}."
        )

    def _make_id(self, *, raw_id: Any, base_id: str | None, section_key: str) -> str:
        base = None
        if isinstance(raw_id, str) and raw_id:
            base = raw_id
        elif isinstance(base_id, str) and base_id:
            base = base_id
        else:
            base = "view"
        return f"{base}:{section_key}"

    def _make_form_id(
        self, *, raw_id: Any, base_id: str | None, section_key: str
    ) -> str:
        base = None
        if isinstance(raw_id, str) and raw_id:
            base = raw_id
        elif isinstance(base_id, str) and base_id:
            base = base_id
        else:
            base = "form"
        return f"{base}.{section_key}"

    def _parse_field_def(self, *, field_id: str, fd: dict[str, Any]) -> ViewFieldDef:
        policy = fd.get("policy")
        if not isinstance(policy, str) or not policy:
            raise ViewSpecValidationError(
                f"inputs.{field_id}.policy must be a non-empty string"
            )

        title_ = fd.get("title")
        if title_ is not None and not isinstance(title_, str):
            raise ViewSpecValidationError(
                f"inputs.{field_id}.title must be a string or null"
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
                f"inputs.{field_id}.required must be a boolean"
            )

        var = fd.get("var")
        if not isinstance(var, str) or not var:
            raise ViewSpecValidationError(
                f"inputs.{field_id}.var must be a non-empty string"
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
                f"inputs.{field_id} hint/default/pattern must be strings"
            )

        ui_raw = fd.get("ui")
        if ui_raw is not None and not isinstance(ui_raw, dict):
            raise ViewSpecValidationError(
                f"inputs.{field_id}.ui must be a mapping or null"
            )

        ui = dict(ui_raw or {})

        # Derivation: masked => secret
        # TODO (minimaler Start; später soll PolicyService hier entscheiden)
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
    # Existing view parsing (unchanged)
    # -----------------------

    def _parse_view(self, raw: dict[str, Any]) -> ViewSpec:
        # ... leave your existing implementation as-is ...
        # (the one in your current file)
        if raw.get("kind") != "view":
            raise ViewSpecValidationError("ViewSpec.kind must be 'view'")

        mode = raw.get("mode", "replace")
        if mode not in ("replace", "append", "patch"):
            raise ViewSpecValidationError(f"Invalid ViewSpec.mode: {mode!r}")

        view_id = raw.get("id")
        if view_id is not None and not isinstance(view_id, str):
            raise ViewSpecValidationError("ViewSpec.id must be a string or null")

        meta = raw.get("meta")
        if meta is not None and not isinstance(meta, dict):
            raise ViewSpecValidationError("ViewSpec.meta must be a mapping or null")

        message_raw = raw.get("message")
        message = None
        if message_raw is not None:
            if not isinstance(message_raw, dict):
                raise ViewSpecValidationError(
                    "ViewSpec.message must be a mapping or null"
                )
            message = self._parse_message_spec_string_only(message_raw)

        input_raw = raw.get("input")
        input_def = None
        if input_raw is not None:
            if not isinstance(input_raw, dict):
                raise ViewSpecValidationError(
                    "ViewSpec.input must be a mapping or null"
                )
            input_def = self._parse_input(input_raw)

        # view_meta = ViewMeta(ui=ViewUI(secret=meta.get("secret")))
        return ViewSpec(
            kind="view",
            mode=mode,
            id=view_id,
            message=message,
            input=input_def,
            meta=meta,
        )

    def _parse_input(self, raw: dict[str, Any]) -> ViewFormDef:
        if raw.get("kind") != "form":
            raise ViewSpecValidationError("ViewSpec.input.kind must be 'form'")

        form_id = raw.get("form_id")
        if not isinstance(form_id, str) or not form_id:
            raise ViewSpecValidationError(
                "ViewSpec.input.form_id must be a non-empty string"
            )

        title = raw.get("title")
        if title is not None and not isinstance(title, str):
            raise ViewSpecValidationError(
                "ViewSpec.input.title must be a string or null"
            )

        meta = raw.get("meta")
        if meta is not None and not isinstance(meta, dict):
            raise ViewSpecValidationError(
                "ViewSpec.input.meta must be a mapping or null"
            )

        fields_raw = raw.get("fields")
        if not isinstance(fields_raw, dict) or not fields_raw:
            raise ViewSpecValidationError(
                "ViewSpec.input.fields must be a non-empty mapping"
            )

        fields: dict[str, ViewFieldDef] = {}
        for field_id, fd in fields_raw.items():
            if not isinstance(field_id, str) or not field_id:
                raise ViewSpecValidationError(
                    "Each field key must be a non-empty string"
                )
            if not isinstance(fd, dict):
                raise ViewSpecValidationError(
                    f"FieldDef for {field_id!r} must be a mapping"
                )

            policy = fd.get("policy")
            if not isinstance(policy, str) or not policy:
                raise ViewSpecValidationError(
                    f"FieldDef.policy for {field_id!r} must be a non-empty string"
                )

            title_ = fd.get("title")
            if title_ is not None and not isinstance(title_, str):
                raise ViewSpecValidationError(
                    f"FieldDef.title for {field_id!r} must be a string or null"
                )

            required = fd.get("required", False)
            if not isinstance(required, bool):
                raise ViewSpecValidationError(
                    f"FieldDef.required for {field_id!r} must be a boolean"
                )

            var = fd.get("var")
            if var is not None and not isinstance(var, str):
                raise ViewSpecValidationError(
                    f"FieldDef.var for {field_id!r} must be a string or null"
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
                    f"FieldDef hint/default/pattern for {field_id!r} must be strings"
                )

            fields[field_id] = ViewFieldDef(
                policy=policy,
                title=title_,
                required=required,
                var=var,
                hint=hint,
                default=default,
                pattern=pattern,
            )

        return ViewFormDef(
            kind="form", form_id=form_id, fields=fields, title=title, meta=meta
        )

    # -----------------------
    # Message parsing (string-only)
    # -----------------------

    def _parse_message_spec_string_only(self, raw: dict[str, Any]) -> MessageSpec:
        """
        Parse MessageSpec while enforcing "string-only" rules:
          - TextBlock.text must be str (not list[Inline])
          - ListBlock.items must be list[str] (not list[list[Inline]])
        """
        # Reuse the existing schema fields of MessageSpec :contentReference[oaicite:6]{index=6}
        if raw.get("kind") is None:
            # allow omitting kind in nested message if you want; enforce it if you prefer
            raw = dict(raw)
            raw["kind"] = "message"

        if raw.get("kind") != "message":
            raise ViewSpecValidationError("ViewSpec.message.kind must be 'message'")

        role = raw.get("role") or "info"
        if role not in ("info", "success", "warning", "error", "help"):
            raise ViewSpecValidationError(f"Invalid MessageSpec.role: {role!r}")

        title = raw.get("title")
        if title is not None and not isinstance(title, str):
            raise ViewSpecValidationError("MessageSpec.title must be a string or null")

        meta = raw.get("meta")
        if meta is not None and not isinstance(meta, dict):
            raise ViewSpecValidationError("MessageSpec.meta must be a mapping or null")

        blocks_raw = raw.get("blocks", [])
        if not isinstance(blocks_raw, list):
            raise ViewSpecValidationError("MessageSpec.blocks must be a list")

        blocks = []
        for b in blocks_raw:
            if not isinstance(b, dict):
                raise ViewSpecValidationError("Each block must be a mapping")
            t = b.get("type")

            # text
            if t == "text":
                text = b.get("text", "")
                if not isinstance(text, str):
                    raise ViewSpecValidationError(
                        "TextBlock.text must be a string (string-only mode)"
                    )
                blocks.append(TextBlock(type="text", text=text))

            # list
            elif t == "list":
                items = b.get("items", [])
                if not isinstance(items, list) or not all(
                    isinstance(x, str) for x in items
                ):
                    raise ViewSpecValidationError(
                        "ListBlock.items must be a list of strings (string-only mode)"
                    )
                blocks.append(ListBlock(type="list", items=items))

            # rule
            elif t == "rule":
                style = b.get("style", "normal")
                if not isinstance(style, str):
                    raise ViewSpecValidationError("RuleBlock.style must be a string")

                if style not in {"subtle", "normal", "strong"}:
                    raise ViewSpecValidationError(
                        f"Invalid rule style: {style!r}. "
                        "Expected one of: subtle, normal, strong."
                    )

                style = cast(Literal["subtle", "normal", "strong"], style)
                blocks.append(RuleBlock(type="rule", style=style))

            # spaces
            elif t == "spacer":
                size = b.get("size", 1)
                if not isinstance(size, int) or size < 0:
                    raise ViewSpecValidationError(
                        "SpacerBlock.size must be a non-negative integer"
                    )
                blocks.append(SpacerBlock(type="spacer", size=size))

            # kv
            elif t == "kv":
                items = b.get("items", [])
                if not isinstance(items, list):
                    raise ViewSpecValidationError(
                        "KvBlock.items must be a list of [key, value] pairs"
                    )
                pairs = []
                for entry in items:
                    if not isinstance(entry, list) or len(entry) != 2:
                        raise ViewSpecValidationError(
                            "Each kv item must be a [key, value] list"
                        )
                    k, v = entry
                    pairs.append((str(k), v))
                blocks.append(KvBlock(type="kv", items=pairs))

            else:
                raise ViewSpecValidationError(f"Unknown block type: {t!r}")

        return MessageSpec(
            kind="message", role=role, title=title, blocks=blocks, meta=meta
        )
