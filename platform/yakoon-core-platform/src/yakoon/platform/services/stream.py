from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, is_dataclass, replace
from typing import Any
from uuid import uuid4

from yakoon.base.models.stream import OutputStreaming, OutputStreamPolicy
from yakoon.base.models.view import ViewSpec
from yakoon.base.runtime.session.session import Session  # ggf. Pfad anpassen


def _clamp(v: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, v))


def _clamp_int(v: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, v))


@dataclass(frozen=True, slots=True)
class _EffectiveStreaming:
    enabled: bool
    id: str | None
    interval: float
    chunk_tokens: int


class OutputStreamService:
    """
    Output streaming service (output-only).
    Emits replace-updates with stable id and cumulatively growing text.

    V1 scope:
    - Stream only the first block that has `.text` (TextBlock-like).
    - Everything else falls back to a single emit.
    """

    MIN_INTERVAL = 0.01
    MAX_INTERVAL = 0.25
    MIN_CHUNK_TOKENS = 1
    MAX_CHUNK_TOKENS = 12

    async def emit(
        self,
        session: Session,
        view: ViewSpec,
        *,
        override: OutputStreaming | None = None,
    ) -> None:
        policy = session.get_output_stream_policy()

        eff = self._effective(policy, override)

        if not eff.enabled:
            await session.emit(view)
            return

        msg = getattr(view, "message", None)
        blocks = getattr(msg, "blocks", None) if msg else None
        blocks = blocks or []
        if not blocks:
            await session.emit(view)
            return

        text_idx, full_text = self._find_first_text_block(blocks)
        if text_idx is None or full_text is None:
            await session.emit(view)
            return

        interval = _clamp(float(eff.interval), self.MIN_INTERVAL, self.MAX_INTERVAL)
        chunk_tokens = _clamp_int(
            int(eff.chunk_tokens), self.MIN_CHUNK_TOKENS, self.MAX_CHUNK_TOKENS
        )

        vid = eff.id or view.id or f"stream:{uuid4().hex}"

        tokens = re.findall(r"\S+|\s+", str(full_text))
        if not tokens:
            out = self._clone_view_with_text(view, vid, "", text_idx, stream="final")
            await session.emit(out)
            return

        acc: list[str] = []
        for pos in range(0, len(tokens), chunk_tokens):
            acc.extend(tokens[pos : pos + chunk_tokens])
            partial = "".join(acc)
            out = self._clone_view_with_text(
                view, vid, partial, text_idx, stream="delta"
            )
            await session.emit(out)
            await asyncio.sleep(interval)

        # ensure final state
        out = self._clone_view_with_text(
            view, vid, str(full_text), text_idx, stream="final"
        )
        await session.emit(out)

    def _effective(
        self,
        policy: OutputStreamPolicy,
        override: OutputStreaming | None,
    ) -> _EffectiveStreaming:

        if override is None:
            return _EffectiveStreaming(
                enabled=policy.enabled,
                id=None,
                interval=policy.interval,
                chunk_tokens=policy.chunk_tokens,
            )

        # Host bleibt Autorität
        enabled = policy.enabled and override.enabled

        interval = (
            override.interval if override.interval is not None else policy.interval
        )

        chunk_tokens = (
            override.chunk_tokens
            if override.chunk_tokens is not None
            else policy.chunk_tokens
        )

        return _EffectiveStreaming(
            enabled=enabled,
            id=override.id,
            interval=interval,
            chunk_tokens=chunk_tokens,
        )

    def _find_first_text_block(
        self, blocks: list[Any]
    ) -> tuple[int | None, str | None]:
        for i, b in enumerate(blocks):
            t = getattr(b, "text", None)
            if t is not None:
                return i, str(t)
        return None, None

    def _clone_view_with_text(
        self,
        view: ViewSpec,
        vid: str,
        text: str,
        idx: int,
        *,
        stream: str,
    ) -> ViewSpec:
        # ViewSpec ist bei euch dataclass => replace ist der richtige Weg.
        msg = view.message
        if msg is None:
            return replace(view, id=vid, mode="replace")

        blocks = list(msg.blocks or [])
        if idx >= len(blocks):
            return replace(view, id=vid, mode="replace")

        b = blocks[idx]

        # TextBlock ist bei euch ebenfalls dataclass -> replace
        if is_dataclass(b):
            nb = replace(b, text=text)
        else:
            # extrem unwahrscheinlich bei euch, aber als Sicherung ok
            try:
                b.text = text
                nb = b
            except Exception:
                nb = b

        blocks[idx] = nb

        # MessageSpec ist dataclass
        msg2 = replace(msg, blocks=blocks, stream=stream)

        # ViewSpec ist dataclass
        return replace(view, id=vid, mode="replace", message=msg2)
