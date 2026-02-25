from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, replace
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

        # no streaming → send full view once
        if not eff.enabled:
            await session.emit(view)
            return

        msg = getattr(view, "message", None)
        blocks = getattr(msg, "blocks", None) if msg else None
        blocks = list(blocks or [])

        if not blocks:
            await session.emit(view)
            return

        interval = _clamp(float(eff.interval), self.MIN_INTERVAL, self.MAX_INTERVAL)
        chunk_tokens = _clamp_int(
            int(eff.chunk_tokens), self.MIN_CHUNK_TOKENS, self.MAX_CHUNK_TOKENS
        )

        vid = eff.id or view.id or f"stream:{uuid4().hex}"

        built: list[Any] = []

        async def emit_snapshot(extra_block=None, stream="delta"):
            out_blocks = list(built)
            if extra_block is not None:
                out_blocks.append(extra_block)

            msg2 = replace(msg, blocks=out_blocks, stream=stream)
            out = replace(view, id=vid, mode="replace", message=msg2)
            await session.emit(out)

        merged = self._merge_consecutive_text_blocks(blocks)
        for block in merged:  # blocks:
            text = getattr(block, "text", None)

            # ---- TEXT BLOCK ----
            if isinstance(text, str):
                tokens = re.findall(r"\S+|\s+", text)
                acc: list[str] = []

                for pos in range(0, len(tokens), chunk_tokens):
                    acc.extend(tokens[pos : pos + chunk_tokens])
                    partial = "".join(acc)

                    partial_block = replace(block, text=partial)
                    await emit_snapshot(extra_block=partial_block, stream="delta")
                    await asyncio.sleep(interval)

                # commit final text block
                built.append(block)
                await emit_snapshot(stream="delta")

            # ---- NON-TEXT BLOCK ----
            else:
                built.append(block)
                await emit_snapshot(stream="delta")

        # final state (no duplication of blocks)
        await emit_snapshot(stream="final")

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

    def _can_merge(self, a, b):
        return (
            getattr(a, "type", None) == "text"
            and getattr(b, "type", None) == "text"
            and getattr(a, "style", None) == getattr(b, "style", None)
        )

    def _merge_consecutive_text_blocks(self, blocks: list):
        merged = []
        buffer = None

        for b in blocks:
            if buffer is not None and self._can_merge(buffer, b):
                # merge text
                merged_text = str(getattr(buffer, "text", "")) + str(
                    getattr(b, "text", "")
                )
                buffer = replace(buffer, text=merged_text)
            else:
                if buffer is not None:
                    merged.append(buffer)
                    buffer = None

                if getattr(b, "text", None) is not None:
                    buffer = b
                else:
                    merged.append(b)

        if buffer is not None:
            merged.append(buffer)

        return merged
