from __future__ import annotations

import asyncio
import random
import re
from collections.abc import Iterator
from dataclasses import dataclass, replace
from typing import Any

from yakoon.base.models.stream import OutputStreaming, OutputStreamPolicy
from yakoon.base.models.view import (
    PatchAppendBlock,
    PatchAppendChild,
    PatchAppendText,
    PatchReset,
    PatchSpec,
    ViewSpec,
)
from yakoon.base.runtime.session.session import Session  # ggf. Pfad anpassen

# -----------------------------
# Effective config (policy + override)
# -----------------------------


@dataclass(frozen=True, slots=True)
class _EffectiveStreaming:
    enabled: bool
    id: str | None
    interval: float
    chunk_size: int
    jitter: float
    punctuation_pause: float


def _clamp(value: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, value))


def _clamp_int(value: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, value))


# -----------------------------
# Chunking (shared for ALL streaming)
# -----------------------------

_WS_TOKENS = re.compile(r"\S+|\s+")


def iter_chunks(text: str, *, min_size: int, max_size: int) -> Iterator[str]:
    """
    Natural-feeling chunk generator:
    - Prefer word boundaries.
    - Keep chunks roughly in [min_size, max_size].
    - Split oversized tokens safely.
    """
    if not text:
        return

    tokens = _WS_TOKENS.findall(text)
    buf = ""

    for tok in tokens:
        # Oversized single token: flush buffer, then hard-split the token
        if len(tok) > max_size:
            if buf:
                yield buf
                buf = ""
            for i in range(0, len(tok), max_size):
                yield tok[i : i + max_size]
            continue

        # Would overflow max_size? emit current buffer
        if buf and (len(buf) + len(tok) > max_size):
            yield buf
            buf = tok
            continue

        buf += tok

        # Reached minimum "natural" size -> emit
        if len(buf) >= min_size:
            yield buf
            buf = ""

    if buf:
        yield buf


# -----------------------------
# Service
# -----------------------------


class OutputStreamService:
    """
    Output streaming service:
    emits ViewSpec(mode="patch") with patch ops.

    V1:
    - Stream text blocks (append_text)
    - Stream list items: append empty list_item, then stream head into "<item_id>.head"
    - Nested blocks under list items are appended as snapshot blocks (can be streamed later)

    Notes:
    - Host is responsible for alias registration "<list_item_id>.head" -> bullet TextWidget.
    """

    # Safety bounds
    MIN_INTERVAL = 0.01
    MAX_INTERVAL = 0.25

    # Chunk sizing:
    # We treat policy.chunk_tokens as a *target max chunk size* (historical name).
    # Then derive a min chunk size from it.
    MIN_CHUNK_SIZE = 8
    MAX_CHUNK_SIZE = 256

    # Feel tuning
    DEFAULT_JITTER = 0.15  # +/- 15%
    DEFAULT_PUNCT_PAUSE = 1.25  # pause multiplier after sentence-ish punctuation

    async def emit(
        self,
        session: Session,
        view: ViewSpec,
        *,
        override: OutputStreaming | None = None,
    ) -> None:
        eff = self._effective(session.get_output_stream_policy(), override)

        if not eff.enabled:
            await session.emit(view)
            return

        msg = getattr(view, "message", None) if view else None
        blocks = list(getattr(msg, "blocks", None) or []) if msg else []
        if not blocks:
            await session.emit(view)
            return

        vid = eff.id or view.id or f"v:{id(view)}"

        async def emit_patch(ops: list[Any], *, final: bool = False) -> None:
            await session.emit(
                replace(
                    view,
                    id=vid,
                    mode="patch",
                    patch=PatchSpec(ops=ops, final=final),
                )
            )

        def pause_for_chunk(chunk: str) -> float:
            base = eff.interval * random.uniform(1.0 - eff.jitter, 1.0 + eff.jitter)
            if chunk and chunk.strip() and chunk.strip()[-1] in ".:!?":
                base *= eff.punctuation_pause
            return base

        def ensure_id(block: Any, suffix: str | int) -> Any:
            """
            Ensure stable id for host registry lookups.
            If block already has id, keep it.
            Else derive from stream view id and suffix.
            """
            bid = getattr(block, "id", None)
            if isinstance(bid, str) and bid:
                return block
            return replace(block, id=f"{vid}:b{suffix}")

        def ensure_item_id(item: Any, list_id: str, index: int) -> Any:
            iid = getattr(item, "id", None)
            if isinstance(iid, str) and iid:
                return item
            return replace(item, id=f"{list_id}:i{index}")

        def can_merge_text(active_style: Any, block: Any) -> bool:
            return (
                getattr(block, "type", None) == "text"
                and isinstance(getattr(block, "text", None), str)
                and getattr(block, "style", None) == active_style
            )

        def chunk_params() -> tuple[int, int]:
            # Derive min/max from a single "chunk_size" value (consistent everywhere).
            max_size = _clamp_int(
                eff.chunk_size, self.MIN_CHUNK_SIZE, self.MAX_CHUNK_SIZE
            )
            min_size = max(self.MIN_CHUNK_SIZE, int(max_size * 0.4))
            return min_size, max_size

        min_size, max_size = chunk_params()

        # Start a new patch stream in the host
        await emit_patch([PatchReset()], final=False)

        active_text_id: str | None = None
        active_style: Any = None

        for idx, raw in enumerate(blocks):
            block = ensure_id(raw, idx)
            btype = getattr(block, "type", None)

            # -----------------------------
            # LIST streaming
            # -----------------------------
            if btype == "list":
                empty_list = replace(block, items=[])
                await emit_patch([PatchAppendBlock(block=empty_list)], final=False)

                list_id = getattr(empty_list, "id", None)
                if not isinstance(list_id, str) or not list_id:
                    # should never happen, but keep stream resilient
                    list_id = getattr(block, "id", "")

                items = list(getattr(block, "items", None) or [])
                for j, item_raw in enumerate(items):
                    item = ensure_item_id(item_raw, list_id, j)

                    head = getattr(item, "head", "")
                    empty_item = replace(item, head="" if isinstance(head, str) else [])

                    await emit_patch(
                        [PatchAppendChild(parent_id=list_id, block=empty_item)],
                        final=False,
                    )

                    item_id = getattr(empty_item, "id", None)
                    if not isinstance(item_id, str) or not item_id:
                        # keep going, but streaming head needs a real id
                        continue

                    head_id = f"{item_id}.head"

                    # Stream head text (string only; inline-head streaming later)
                    if isinstance(head, str) and head:
                        for chunk in iter_chunks(
                            head, min_size=min_size, max_size=max_size
                        ):
                            await emit_patch(
                                [PatchAppendText(block_id=head_id, text=chunk)],
                                final=False,
                            )
                            await asyncio.sleep(pause_for_chunk(chunk))

                    # Nested blocks: snapshot append for now (can be streamed later)
                    nested = getattr(item, "blocks", None)
                    if nested:
                        for k, child_raw in enumerate(nested):
                            child = ensure_id(child_raw, f"{item_id}:{k}")
                            await emit_patch(
                                [PatchAppendChild(parent_id=item_id, block=child)],
                                final=False,
                            )

                active_text_id = None
                active_style = None
                continue

            # -----------------------------
            # KV streaming
            # -----------------------------
            if btype == "kv":
                empty_kv = replace(block, items=[])
                await emit_patch([PatchAppendBlock(block=empty_kv)], final=False)

                kv_id = getattr(empty_kv, "id", None)
                if not isinstance(kv_id, str) or not kv_id:
                    kv_id = getattr(block, "id", "")

                items = list(getattr(block, "items", None) or [])
                for j, item_raw in enumerate(items):
                    item = ensure_item_id(item_raw, kv_id, j)

                    key = str(getattr(item, "key", "") or "")
                    value = getattr(item, "value", None)

                    # append empty kv_item first
                    if isinstance(value, str):
                        empty_item = replace(item, key=key, value="")
                    else:
                        empty_item = replace(item, key=key, value=[])

                    await emit_patch(
                        [PatchAppendChild(parent_id=kv_id, block=empty_item)],
                        final=False,
                    )

                    item_id = getattr(empty_item, "id", None)
                    if not isinstance(item_id, str) or not item_id:
                        continue

                    value_id = f"{item_id}.value"

                    # stream string value
                    if isinstance(value, str) and value:
                        for chunk in iter_chunks(
                            value, min_size=min_size, max_size=max_size
                        ):
                            await emit_patch(
                                [PatchAppendText(block_id=value_id, text=chunk)],
                                final=False,
                            )
                            await asyncio.sleep(pause_for_chunk(chunk))

                    # nested blocks snapshot
                    nested = getattr(item, "blocks", None)
                    if nested:
                        for k, child_raw in enumerate(nested):
                            child = ensure_id(child_raw, f"{item_id}:{k}")
                            await emit_patch(
                                [PatchAppendChild(parent_id=item_id, block=child)],
                                final=False,
                            )

                    # value as blocks (future-proof)
                    if isinstance(value, list):
                        for k, child_raw in enumerate(value):
                            child = ensure_id(child_raw, f"{item_id}:{k}")
                            await emit_patch(
                                [PatchAppendChild(parent_id=item_id, block=child)],
                                final=False,
                            )

                active_text_id = None
                active_style = None
                continue

            # -----------------------------
            # TEXT streaming (merge adjacent same-style blocks)
            # -----------------------------
            text = getattr(block, "text", None)
            if btype == "text" and isinstance(text, str):
                bstyle = getattr(block, "style", None)

                starting_new = (active_text_id is None) or (
                    not can_merge_text(active_style, block)
                )

                if starting_new:
                    empty = replace(block, text="")
                    await emit_patch([PatchAppendBlock(block=empty)], final=False)
                    active_text_id = getattr(empty, "id", None)
                    active_style = bstyle
                    prefix = ""
                else:
                    prefix = "\n" if (text and not text.startswith("\n")) else ""

                tid = active_text_id or getattr(block, "id", "")
                full = prefix + text

                for chunk in iter_chunks(full, min_size=min_size, max_size=max_size):
                    await emit_patch(
                        [PatchAppendText(block_id=tid, text=chunk)], final=False
                    )
                    await asyncio.sleep(pause_for_chunk(chunk))

                continue

            # -----------------------------
            # NON-TEXT (snapshot)
            # -----------------------------
            active_text_id = None
            active_style = None
            await emit_patch([PatchAppendBlock(block=block)], final=False)

        await emit_patch([], final=True)

    def _effective(
        self,
        policy: OutputStreamPolicy,
        override: OutputStreaming | None,
    ) -> _EffectiveStreaming:
        # enabled: host policy remains authority
        if override is None:
            enabled = bool(policy.enabled)
            interval = float(policy.interval)
            chunk_size = int(policy.chunk_tokens)  # historical name, now used as size
            sid = None
        else:
            enabled = bool(policy.enabled) and bool(override.enabled)
            interval = float(
                override.interval if override.interval is not None else policy.interval
            )
            chunk_size = int(
                override.chunk_tokens
                if override.chunk_tokens is not None
                else policy.chunk_tokens
            )
            sid = override.id

        interval = _clamp(interval, self.MIN_INTERVAL, self.MAX_INTERVAL)

        # chunk_size must remain within safe bounds; semantics: "max chunk size"
        chunk_size = _clamp_int(chunk_size, self.MIN_CHUNK_SIZE, self.MAX_CHUNK_SIZE)

        return _EffectiveStreaming(
            enabled=enabled,
            id=sid,
            interval=interval,
            chunk_size=chunk_size,
            jitter=self.DEFAULT_JITTER,
            punctuation_pause=self.DEFAULT_PUNCT_PAUSE,
        )
