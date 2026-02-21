from __future__ import annotations

from yakoon.base import ports
from yakoon.base.directories.service import ServiceDirectory
from yakoon.base.models.prompt import PromptResult
from yakoon.base.models.view import ViewSpec
from yakoon.base.runtime.session.session import Session
from yakoon.base.runtime.session.views import v_error
from yakoon.platform.settings import settings


class InputService:
    """
    Unified interaction layer (view-only).

    Contract:
      - ask_view(session, view) -> PromptResult
      - DialogService waits on view and returns raw dict[str, object]
      - Policy validation is performed directly via PolicyService using policy key.
    """

    def __init__(self, services: ServiceDirectory):
        self._dialogs = services.get(ports.DialogService)
        self._policy = services.get(ports.PolicyService)

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

        if not isinstance(aliases, dict) or not all(
            isinstance(k, str) and isinstance(v, str) for k, v in aliases.items()
        ):
            aliases = {}
        if not isinstance(order, list) or not all(isinstance(x, str) for x in order):
            order = list(fields_def.keys())

        while True:
            raw = await self._dialogs.wait_view(
                session,
                view=view,
                timeout=settings.network.prompt_timed_out,
            )

            errors = []
            out: dict[str, object] = {}

            for key, fd in fields_def.items():
                policy_key = fd.policy
                required = bool(fd.required)
                val = raw.get(key)

                if not isinstance(policy_key, str) or not policy_key:
                    errors.append(_err(key, "Missing policy"))
                    continue

                if required and (val is None or val == ""):
                    errors.append(_err(key, "Required"))
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

                    # Optional typed validators (falls du sie modelliert hast)
                    validators = getattr(fd, "validators", ()) or ()
                    for vkey in validators:
                        validator = self._policy.get_validator(vkey)
                        vres = await validator(
                            session=session,
                            field={"key": key, "policy": policy_key},
                            value=coerced,
                            values=out,
                        )
                        if not vres.ok:
                            errors.extend(vres.errors)

                    out[key] = coerced
                else:
                    errors.extend(res.errors)

            unknown = set(raw.keys()) - set(fields_def.keys())
            if unknown:
                errors.append(_err("form", f"Unknown fields: {sorted(unknown)}"))

            if not errors:
                return PromptResult(out, aliases, order)

            for e in errors:
                await session.emit(
                    v_error(
                        f"[{getattr(e, 'field_key', 'form')}] {getattr(e, 'message', str(e))}"
                    )
                )


def _err(field_key: str, message: str):
    return type("Err", (), {"field_key": field_key, "message": message})()
