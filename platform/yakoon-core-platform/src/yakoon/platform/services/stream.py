from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass, replace
from typing import Any

from yakoon.base.models.stream import OutputStreaming, OutputStreamPolicy
from yakoon.base.models.view import (
    PatchAppendBlock,
    PatchAppendText,
    PatchReset,
    PatchSpec,
    ViewSpec,
)
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

        # streaming disabled -> emit full view once
        if not eff.enabled:
            await session.emit(view)
            return

        msg = getattr(view, "message", None) if view else None
        blocks = list(getattr(msg, "blocks", None) or []) if msg else []
        if not blocks:
            await session.emit(view)
            return

        interval = _clamp(float(eff.interval), self.MIN_INTERVAL, self.MAX_INTERVAL)
        chunk_tokens = _clamp_int(
            int(eff.chunk_tokens), self.MIN_CHUNK_TOKENS, self.MAX_CHUNK_TOKENS
        )

        # stable view id for whole stream
        vid = eff.id or view.id or f"v:{id(view)}"

        def emit_patch(ops, *, final: bool = False):
            return session.emit(
                replace(
                    view,
                    id=vid,
                    mode="patch",
                    patch=PatchSpec(ops=ops, final=final),
                )
            )

        def ensure_id(b: Any, idx: int) -> Any:
            bid = getattr(b, "id", None)
            if bid:
                idx = bid
            #    return b
            # stable enough; bound to view id + index
            return replace(b, id=f"{vid}:b{idx}")

        def can_merge_text(active_style: Any, b: Any) -> bool:
            return (
                getattr(b, "type", None) == "text"
                and isinstance(getattr(b, "text", None), str)
                and getattr(b, "style", None) == active_style
            )

        # reset stream in host container
        await emit_patch([PatchReset()], final=False)

        active_text_id: str | None = None
        active_style: Any = None

        for idx, block in enumerate(blocks):
            block = ensure_id(block, idx)
            btype = getattr(block, "type", None)
            text = getattr(block, "text", None)

            # TEXT (string) -> stream via append_text to a known block_id
            if btype == "text" and isinstance(text, str):
                bstyle = getattr(block, "style", None)

                starting_new = (active_text_id is None) or (
                    not can_merge_text(active_style, block)
                )

                if starting_new:
                    # open an empty text container in the host
                    empty = replace(block, text="")
                    await emit_patch([PatchAppendBlock(block=empty)], final=False)
                    active_text_id = getattr(empty, "id", None)
                    active_style = bstyle
                    prefix = ""
                else:
                    # continue same text block, separate paragraphs/items
                    prefix = "\n" if (text and not text.startswith("\n")) else ""

                # stream the content in chunks
                tokens = re.findall(r"\S+|\s+", prefix + text)
                # active_text_id must exist because we opened empty above
                tid = active_text_id or getattr(block, "id", "")
                for pos in range(0, len(tokens), chunk_tokens):
                    chunk = "".join(tokens[pos : pos + chunk_tokens])
                    await emit_patch(
                        [PatchAppendText(block_id=tid, text=chunk)], final=False
                    )
                    await asyncio.sleep(interval)

                continue

            # NON-TEXT -> append once
            active_text_id = None
            active_style = None
            await emit_patch([PatchAppendBlock(block=block)], final=False)

        # final marker
        await emit_patch([], final=True)

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
