from __future__ import annotations

from dataclasses import replace

from yakoon.base.capabilities.interaction import DialogService, PolicyService
from yakoon.base.capabilities.presenters import PromptResult
from yakoon.base.runtime.services import ServiceDirectory
from yakoon.base.runtime.sessions.session import Session
from yakoon.base.ui import ViewSpec, v_error
from yakoon.platform.settings import settings


class DefaultInputService:
    """
    Unified interaction layer (view-only).

    Modes:
      - prompt (stepwise): Engine asks one field at a time and validates immediately.
      - form (batch): Engine validates submitted dict and returns field errors.
    """

    def __init__(self, services: ServiceDirectory):
        self._dialogs = services.get(DialogService)
        self._policy = services.get(PolicyService)

    async def ask_view(self, session: Session, view: ViewSpec) -> PromptResult:
        input_def = view.input
        if input_def is None:
            raise TypeError("View has no input")
        if input_def.kind != "form":
            raise TypeError("Only input.kind='form' supported")

        fields_def = input_def.fields
        if not fields_def:
            raise TypeError("View.input.fields must be a non-empty mapping")

        meta = input_def.meta or {}
        aliases = meta.get("aliases") or {}
        order = meta.get("order") or list(fields_def.keys())

        input_mode = input_def.input_mode or "prompt"

        if not isinstance(aliases, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in aliases.items()
        ):
            aliases = {}
        if not isinstance(order, list) or not all(isinstance(x, str) for x in order):
            order = list(fields_def.keys())
        if input_mode not in ("prompt", "form"):
            input_mode = "prompt"

        if input_mode == "form":
            out = await self._ask_batch(session, view, order)
        else:
            out = await self._ask_stepwise(session, view, order)

        return PromptResult(out, aliases, order)

    # ----------------------------
    # strategies
    # ----------------------------

    async def _ask_batch(
        self, session: Session, view: ViewSpec, order: list[str]
    ) -> dict[str, object]:
        """Batch: host submits a dict for the whole form; we validate everything."""
        input_def = view.input
        assert input_def is not None

        while True:
            raw = await self._dialogs.wait_view(
                session,
                view=view,
                timeout=settings.network.prompt_timed_out,
            )

            out, errors = await self._validate_all(session, input_def, raw, order)

            unknown = set(raw.keys()) - set(input_def.fields.keys())
            if unknown:
                errors.setdefault("form", []).append(
                    f"Unknown fields: {sorted(unknown)}"
                )

            if not errors:
                return out

            await self._emit_errors(session, errors)

    async def _ask_stepwise(
        self, session: Session, view: ViewSpec, order: list[str]
    ) -> dict[str, object]:
        """Prompt: ask & validate field-by-field; next field only after success."""
        input_def = view.input
        assert input_def is not None

        out: dict[str, object] = {}

        for key in order:
            if key not in input_def.fields:
                # ignore unknown order entries
                continue

            while True:
                step_view = self._with_only_field(view, key)

                raw = await self._dialogs.wait_view(
                    session,
                    view=step_view,
                    timeout=settings.network.prompt_timed_out,
                )

                # validate only this key (but allow validators to see current `out`)
                partial_out, errors = await self._validate_all(
                    session,
                    input_def,
                    raw,
                    order=[key],
                    values_so_far=out,
                )

                unknown = set(raw.keys()) - {key}
                if unknown:
                    errors.setdefault("form", []).append(
                        f"Unknown fields: {sorted(unknown)}"
                    )

                if errors:
                    await self._emit_errors(session, errors)
                    continue

                # ok: merge coerced value
                if key in partial_out:
                    out[key] = partial_out[key]
                break

        return out

    # ----------------------------
    # helpers
    # ----------------------------

    def _with_only_field(self, view: ViewSpec, key: str) -> ViewSpec:
        input_def = view.input
        if input_def is None:
            return view
        fd = input_def.fields.get(key)
        if fd is None:
            return view
        new_input = replace(input_def, fields={key: fd})
        return replace(view, input=new_input)

    async def _validate_all(
        self,
        session: Session,
        input_def,
        raw: dict[str, object],
        order: list[str],
        *,
        values_so_far: dict[str, object] | None = None,
    ) -> tuple[dict[str, object], dict[str, list[str]]]:
        """
        Shared validation used by both strategies.
        Returns:
          - coerced values (only for keys in `order`)
          - errors per field key
        """
        values_so_far = values_so_far or {}

        out: dict[str, object] = {}
        errors: dict[str, list[str]] = {}

        fields_def = input_def.fields

        for key in order:
            fd = fields_def.get(key)
            if fd is None:
                continue

            policy_key = fd.policy
            required = bool(fd.required)
            val = raw.get(key)

            if not isinstance(policy_key, str) or not policy_key:
                errors.setdefault(key, []).append("Missing policy")
                continue

            if required and (val is None or val == ""):
                errors.setdefault(key, []).append("Required")
                continue

            try:
                res = self._policy.validate(policy_key=policy_key, raw=val)
            except KeyError:
                await session.emit(v_error(f"[{key}] Unknown policy: {policy_key}"))
                raise
            except Exception as exc:  # noqa: BLE001
                await session.emit(
                    v_error(
                        f"[{key}] Policy error: {policy_key} ({type(exc).__name__})"
                    )
                )
                raise

            if res.ok:
                coerced = res.value

                # Optional async validators (if modeled on fd)
                validators = getattr(fd, "validators", ()) or ()
                for vkey in validators:
                    validator = self._policy.get_validator(vkey)
                    vres = await validator(
                        session=session,
                        field={"key": key, "policy": policy_key},
                        value=coerced,
                        values={**values_so_far, **out},
                    )
                    if not vres.ok:
                        # support both: list[str] or list[Err-like]
                        for e in getattr(vres, "errors", []) or []:
                            msg = getattr(e, "message", None) or str(e)
                            errors.setdefault(key, []).append(msg)

                out[key] = coerced
            else:
                for e in getattr(res, "errors", []) or []:
                    msg = getattr(e, "message", None) or str(e)
                    errors.setdefault(key, []).append(msg)

        return out, errors

    async def _emit_errors(
        self, session: Session, errors: dict[str, list[str]]
    ) -> None:
        # stable order: field errors first, then form-level
        for key, msgs in errors.items():
            for msg in msgs:
                await session.emit(
                    v_error(
                        f"[{key}] {msg}",
                        error_kind="validation",
                    )
                )
