from __future__ import annotations

from dataclasses import dataclass, replace

from .context import InputContext


@dataclass(frozen=True, slots=True)
class InputEvent:
    data: str
    tokens: list[str] | None = None
    context: InputContext | None = None
    batch_id: str | None = None

    payload: object | None = None

    @classmethod
    def from_raw(cls, data: str, context=None, batch_id=None):
        return cls(data, [], context, batch_id)

    def to_values(self) -> dict[str, str]:
        result: dict[str, str] = {}
        sources = [self.data] + (self.tokens or [])
        for item in sources:
            for sep in ("=", ":"):
                if sep in item:
                    key, _, value = item.partition(sep)
                    result[key.strip()] = value.strip()
                    break
        return result

    def update(
        self,
        *,
        data: str | None = None,
        tokens: list[str] | None = None,
    ) -> InputEvent:

        return replace(
            self,
            data=data if data is not None else self.data,
            tokens=tokens if tokens is not None else self.tokens,
        )
