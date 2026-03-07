from __future__ import annotations

import asyncio
import random
import re
from collections.abc import Iterator
from dataclasses import dataclass, replace
from typing import Any

from yakoon.base.models.stream import OutputStreaming, OutputStreamPolicy
from yakoon.base.runtime.sessions import Session  # ggf. Pfad anpassen
from yakoon.base.ui import (
    PatchAppendBlock,
    PatchAppendChild,
    PatchAppendText,
    PatchReset,
    PatchSpec,
    ViewSpec,
)

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

    Streaming rules (no exceptions):
    - list / kv are always streamed structurally (container first, then items, then nested blocks)
    - nested list / kv use the exact same logic as top-level (recursive)
    """

    # Safety bounds
    MIN_INTERVAL = 0.05
    MAX_INTERVAL = 0.25

    # Chunk sizing:
    MIN_CHUNK_SIZE = 8
    MAX_CHUNK_SIZE = 96

    # Feel tuning
    DEFAULT_JITTER = 0.10  # +/- 10%
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

        # -----------------------------
        # Time-based text batching (ChatGPT-like UI cadence)
        # -----------------------------
        import time

        FLUSH_INTERVAL = 1.0 / 30.0  # ~30 FPS UI updates
        pending_text: dict[str, str] = {}
        last_flush: float = time.monotonic()

        def is_punctuation_pause(chunk: str) -> bool:
            # Flush before long "thinking" pauses so punctuation becomes visible first.
            if not chunk:
                return False
            tail = chunk[-1]
            return tail in ".!?…:;" or tail == "\n"

        async def flush_text(*, final: bool = False) -> None:
            """Emit all queued PatchAppendText ops as a single patch."""
            nonlocal pending_text, last_flush
            if not pending_text and not final:
                return
            ops = [
                PatchAppendText(block_id=k, text=v)
                for k, v in pending_text.items()
                if v
            ]
            pending_text = {}
            last_flush = time.monotonic()
            await emit_patch(ops, final=final)

        async def queue_text(block_id: str, chunk: str) -> None:
            """Queue a chunk and flush at a steady UI cadence."""
            nonlocal pending_text, last_flush
            if not chunk:
                return
            pending_text[block_id] = pending_text.get(block_id, "") + chunk

            now = time.monotonic()
            if (now - last_flush) >= FLUSH_INTERVAL:
                await flush_text(final=False)

        def ensure_id(block: Any, suffix: str | int) -> Any:
            bid = getattr(block, "id", None)
            if isinstance(bid, str) and bid:
                return block
            return replace(block, id=f"{vid}:b{suffix}")

        def ensure_item_id(item: Any, parent_id: str, index: int) -> Any:
            iid = getattr(item, "id", None)
            if isinstance(iid, str) and iid:
                return item
            return replace(item, id=f"{parent_id}:i{index}")

        def can_merge_text(active_style: Any, block: Any) -> bool:
            return (
                getattr(block, "type", None) == "text"
                and isinstance(getattr(block, "text", None), str)
                and getattr(block, "style", None) == active_style
            )

        def chunk_params() -> tuple[int, int]:
            max_size = _clamp_int(
                eff.chunk_size, self.MIN_CHUNK_SIZE, self.MAX_CHUNK_SIZE
            )
            min_size = max(self.MIN_CHUNK_SIZE, int(max_size * 0.4))
            return min_size, max_size

        min_size, max_size = chunk_params()

        # -----------------------------
        # Unified recursive streaming helpers
        # -----------------------------

        async def append_block_or_child(parent_id: str | None, block: Any) -> None:
            await flush_text(final=False)  # keep text ops ordered before structural ops
            """Append as root block if parent_id is None; else append as child under parent_id."""
            if parent_id is None:
                await emit_patch([PatchAppendBlock(block=block)], final=False)
            else:
                await emit_patch(
                    [PatchAppendChild(parent_id=parent_id, block=block)], final=False
                )

        async def stream_any(
            parent_id: str | None, raw_block: Any, suffix: str | int
        ) -> None:
            """
            Stream any block under parent_id (or root if parent_id is None).
            Containers (list/kv) are streamed structurally, recursively.
            Everything else is appended as a single block (snapshot for that block type).
            """
            block = ensure_id(raw_block, suffix)
            btype = getattr(block, "type", None)

            if btype == "list":
                await stream_list(parent_id, block)
                return

            if btype == "kv":
                await stream_kv(parent_id, block)
                return

            # text blocks at root (or nested) can still be appended as blocks;
            # their internal text streaming is handled by the outer loop only for top-level.
            await append_block_or_child(parent_id, block)

        async def stream_list(parent_id: str | None, block: Any) -> None:
            """
            Stream list structurally (works for root and nested):
            - append empty list container
            - append empty list_item children
            - stream head into '<item_id>.head'
            - recurse into nested blocks
            """
            empty_list = replace(block, items=[])
            await append_block_or_child(parent_id, empty_list)

            list_id = getattr(empty_list, "id", None)
            if not isinstance(list_id, str) or not list_id:
                list_id = getattr(block, "id", "")

            items = list(getattr(block, "items", None) or [])
            for j, item_raw in enumerate(items):
                item = ensure_item_id(item_raw, list_id, j)

                head = getattr(item, "head", "")
                empty_item = replace(item, head="" if isinstance(head, str) else [])

                await emit_patch(
                    [PatchAppendChild(parent_id=list_id, block=empty_item)], final=False
                )

                item_id = getattr(empty_item, "id", None)
                if not isinstance(item_id, str) or not item_id:
                    continue

                head_id = f"{item_id}.head"

                # stream head (string only)
                if isinstance(head, str) and head:
                    for chunk in iter_chunks(
                        head, min_size=min_size, max_size=max_size
                    ):
                        await queue_text(head_id, chunk)
                        if is_punctuation_pause(chunk):
                            await flush_text(final=False)
                        await asyncio.sleep(pause_for_chunk(chunk))
                    await flush_text(final=False)

                # recurse nested blocks (including nested list/kv)
                nested = getattr(item, "blocks", None)
                if nested:
                    for k, child_raw in enumerate(nested):
                        await stream_any(item_id, child_raw, suffix=f"{item_id}:{k}")

        async def stream_kv(parent_id: str | None, block: Any) -> None:
            """
            Stream kv structurally (works for root and nested):
            - append empty kv container
            - append empty kv_item children
            - stream string value into '<item_id>.value'
            - recurse into nested blocks (blocks + list values)
            """
            empty_kv = replace(block, items=[])
            await append_block_or_child(parent_id, empty_kv)

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
                    [PatchAppendChild(parent_id=kv_id, block=empty_item)], final=False
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
                        await queue_text(value_id, chunk)
                        if is_punctuation_pause(chunk):
                            await flush_text(final=False)
                        await asyncio.sleep(pause_for_chunk(chunk))
                    await flush_text(final=False)

                # recurse nested blocks in kv_item.blocks
                nested = getattr(item, "blocks", None)
                if nested:
                    for k, child_raw in enumerate(nested):
                        await stream_any(item_id, child_raw, suffix=f"{item_id}:{k}")

                # value as blocks
                if isinstance(value, list):
                    for k, child_raw in enumerate(value):
                        await stream_any(item_id, child_raw, suffix=f"{item_id}:{k}")

        # Start a new patch stream in the host
        await emit_patch([PatchReset()], final=False)

        active_text_id: str | None = None
        active_style: Any = None

        for idx, raw in enumerate(blocks):
            block = ensure_id(raw, idx)
            btype = getattr(block, "type", None)

            # -----------------------------
            # LIST streaming (root)
            # -----------------------------
            if btype == "list":
                await stream_list(None, block)
                active_text_id = None
                active_style = None
                continue

            # -----------------------------
            # KV streaming (root)
            # -----------------------------
            if btype == "kv":
                await stream_kv(None, block)
                active_text_id = None
                active_style = None
                continue

            # -----------------------------
            # TEXT streaming (merge adjacent same-style blocks) (root)
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
                    await queue_text(tid, chunk)
                    if is_punctuation_pause(chunk):
                        await flush_text(final=False)
                    await asyncio.sleep(pause_for_chunk(chunk))
                await flush_text(final=False)

                continue

            # -----------------------------
            # NON-TEXT (snapshot append of that block type)
            # -----------------------------
            active_text_id = None
            active_style = None
            await emit_patch([PatchAppendBlock(block=block)], final=False)

        await flush_text(final=False)
        await emit_patch([], final=True)

    def _effective(
        self,
        policy: OutputStreamPolicy,
        override: OutputStreaming | None,
    ) -> _EffectiveStreaming:
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
        chunk_size = _clamp_int(chunk_size, self.MIN_CHUNK_SIZE, self.MAX_CHUNK_SIZE)

        return _EffectiveStreaming(
            enabled=enabled,
            id=sid,
            interval=interval,
            chunk_size=chunk_size,
            jitter=self.DEFAULT_JITTER,
            punctuation_pause=self.DEFAULT_PUNCT_PAUSE,
        )
