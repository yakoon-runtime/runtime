from __future__ import annotations

import asyncio
import random
import re
import time
from collections.abc import Iterator
from dataclasses import dataclass, replace
from typing import Any

from yakoon.base.runtime import Session
from yakoon.base.ui import (
    Block,
    OutputStreaming,
    OutputStreamPolicy,
    PatchAppendBlock,
    PatchAppendChild,
    PatchAppendText,
    PatchReset,
    PatchSpec,
    ViewEvent,
    ViewSpec,
)


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


_WS_TOKENS = re.compile(r"\S+|\s+")


def iter_chunks(text: str, *, min_size: int, max_size: int) -> Iterator[str]:
    if not text:
        return

    tokens = _WS_TOKENS.findall(text)
    buf = ""

    for tok in tokens:
        if len(tok) > max_size:
            if buf:
                yield buf
                buf = ""
            for i in range(0, len(tok), max_size):
                yield tok[i : i + max_size]
            continue

        if buf and (len(buf) + len(tok) > max_size):
            yield buf
            buf = tok
            continue

        buf += tok

        if len(buf) >= min_size:
            yield buf
            buf = ""

    if buf:
        yield buf


class DefaultOutputStreamService:
    """
    Block-oriented output streamer.

    Transport contract:
      - hosts receive ViewEvent only
      - begin_view(...) emits header + reset patch
      - emit_block(...) emits patch-only events
      - finish_view(...) emits final patch-only event

    The streamer never emits ViewSpec directly.
    """

    MIN_INTERVAL = 0.05
    MAX_INTERVAL = 0.25

    MIN_CHUNK_SIZE = 8
    MAX_CHUNK_SIZE = 96

    DEFAULT_JITTER = 0.10
    DEFAULT_PUNCT_PAUSE = 1.25
    FLUSH_INTERVAL = 1.0 / 30.0

    async def begin_view(
        self,
        session: Session,
        view: ViewSpec,
        *,
        override: OutputStreaming | None = None,
    ) -> None:
        eff = self._effective(session.get_output_stream_policy(), override)
        vid = eff.id or view.id or f"v:{id(view)}"

        await session.emit(
            ViewEvent(
                id=vid,
                header=view.header,
                patch=PatchSpec(ops=[PatchReset()], final=False),
            )
        )

    async def finish_view(
        self,
        session: Session,
        view: ViewSpec,
        *,
        override: OutputStreaming | None = None,
    ) -> None:
        eff = self._effective(session.get_output_stream_policy(), override)
        if not eff.enabled:
            return

        vid = eff.id or view.id or f"v:{id(view)}"
        await session.emit(
            ViewEvent(
                id=vid,
                header=None,
                patch=PatchSpec(ops=[], final=True),
            )
        )

    async def emit_block(
        self,
        session: Session,
        *,
        view: ViewSpec,
        block: Block,
        override: OutputStreaming | None = None,
        parent_id: str | None = None,
        suffix: str | int = 0,
    ) -> None:
        eff = self._effective(session.get_output_stream_policy(), override)
        vid = eff.id or view.id or f"v:{id(view)}"

        if not eff.enabled:
            op = (
                PatchAppendChild(parent_id=parent_id, block=block)
                if parent_id is not None
                else PatchAppendBlock(block=block)
            )
            await session.emit(
                ViewEvent(
                    id=vid,
                    header=None,
                    patch=PatchSpec(ops=[op], final=True),
                )
            )
            return

        min_size, max_size = self._chunk_params(eff)

        pending_text: dict[str, str] = {}
        last_flush: float = time.monotonic()

        async def emit_ops(ops: list[Any], *, final: bool = False) -> None:
            await session.emit(
                ViewEvent(
                    id=vid,
                    header=None,
                    patch=PatchSpec(ops=ops, final=final),
                )
            )

        def pause_for_chunk(chunk: str) -> float:
            base = eff.interval * random.uniform(1.0 - eff.jitter, 1.0 + eff.jitter)
            if chunk and chunk.strip() and chunk.strip()[-1] in ".:!?":
                base *= eff.punctuation_pause
            return base

        def is_punctuation_pause(chunk: str) -> bool:
            if not chunk:
                return False
            return chunk[-1] in ".!?…:;\n"

        async def flush_text() -> None:
            nonlocal pending_text, last_flush
            if not pending_text:
                return
            ops = [
                PatchAppendText(block_id=block_id, text=text)
                for block_id, text in pending_text.items()
                if text
            ]
            pending_text = {}
            last_flush = time.monotonic()
            if ops:
                await emit_ops(ops, final=False)

        async def queue_text(block_id: str, chunk: str) -> None:
            nonlocal pending_text, last_flush
            if not chunk:
                return
            pending_text[block_id] = pending_text.get(block_id, "") + chunk
            now = time.monotonic()
            if (now - last_flush) >= self.FLUSH_INTERVAL:
                await flush_text()

        async def append_block_or_child(
            target_parent_id: str | None, out_block: Any
        ) -> None:
            await flush_text()
            if target_parent_id is None:
                await emit_ops([PatchAppendBlock(block=out_block)], final=False)
            else:
                await emit_ops(
                    [PatchAppendChild(parent_id=target_parent_id, block=out_block)],
                    final=False,
                )

        def ensure_id(raw_block: Any, local_suffix: str | int) -> Any:
            bid = getattr(raw_block, "id", None)
            if isinstance(bid, str) and bid:
                return raw_block
            return replace(raw_block, id=f"{vid}:b{local_suffix}")

        def ensure_item_id(item: Any, owner_id: str, index: int) -> Any:
            iid = getattr(item, "id", None)
            if isinstance(iid, str) and iid:
                return item
            return replace(item, id=f"{owner_id}:i{index}")

        async def stream_any(
            target_parent_id: str | None,
            raw_block: Any,
            local_suffix: str | int,
        ) -> None:
            out_block = ensure_id(raw_block, local_suffix)
            btype = getattr(out_block, "type", None)

            if btype == "text":
                await stream_text(target_parent_id, out_block)
                return
            if btype == "list":
                await stream_list(target_parent_id, out_block)
                return
            if btype == "kv":
                await stream_kv(target_parent_id, out_block)
                return

            await append_block_or_child(target_parent_id, out_block)

        async def stream_text(target_parent_id: str | None, out_block: Any) -> None:
            text = getattr(out_block, "text", None)
            if not isinstance(text, str):
                await append_block_or_child(target_parent_id, out_block)
                return

            empty = replace(out_block, text="")
            await append_block_or_child(target_parent_id, empty)

            block_id = getattr(empty, "id", None)
            if not isinstance(block_id, str) or not block_id:
                return

            for chunk in iter_chunks(text, min_size=min_size, max_size=max_size):
                await queue_text(block_id, chunk)
                if is_punctuation_pause(chunk):
                    await flush_text()
                await asyncio.sleep(pause_for_chunk(chunk))

            await flush_text()

        async def stream_list(target_parent_id: str | None, out_block: Any) -> None:
            empty_list = replace(out_block, items=[])
            await append_block_or_child(target_parent_id, empty_list)

            list_id = getattr(empty_list, "id", None)
            if not isinstance(list_id, str) or not list_id:
                return

            items = list(getattr(out_block, "items", None) or [])
            for j, item_raw in enumerate(items):
                item = ensure_item_id(item_raw, list_id, j)

                head = getattr(item, "head", "")
                empty_item = replace(item, head="" if isinstance(head, str) else [])

                await emit_ops(
                    [PatchAppendChild(parent_id=list_id, block=empty_item)],
                    final=False,
                )

                item_id = getattr(empty_item, "id", None)
                if not isinstance(item_id, str) or not item_id:
                    continue

                head_id = f"{item_id}.head"
                if isinstance(head, str) and head:
                    for chunk in iter_chunks(
                        head, min_size=min_size, max_size=max_size
                    ):
                        await queue_text(head_id, chunk)
                        if is_punctuation_pause(chunk):
                            await flush_text()
                        await asyncio.sleep(pause_for_chunk(chunk))
                    await flush_text()

                nested = getattr(item, "blocks", None)
                if nested:
                    for k, child_raw in enumerate(nested):
                        await stream_any(
                            item_id, child_raw, local_suffix=f"{item_id}:{k}"
                        )

        async def stream_kv(target_parent_id: str | None, out_block: Any) -> None:
            empty_kv = replace(out_block, items=[])
            await append_block_or_child(target_parent_id, empty_kv)

            kv_id = getattr(empty_kv, "id", None)
            if not isinstance(kv_id, str) or not kv_id:
                return

            items = list(getattr(out_block, "items", None) or [])
            for j, item_raw in enumerate(items):
                item = ensure_item_id(item_raw, kv_id, j)

                key = str(getattr(item, "key", "") or "")
                value = getattr(item, "value", None)

                if isinstance(value, str):
                    empty_item = replace(item, key=key, value="")
                else:
                    empty_item = replace(item, key=key, value=[])

                await emit_ops(
                    [PatchAppendChild(parent_id=kv_id, block=empty_item)],
                    final=False,
                )

                item_id = getattr(empty_item, "id", None)
                if not isinstance(item_id, str) or not item_id:
                    continue

                value_id = f"{item_id}.value"

                if isinstance(value, str) and value:
                    for chunk in iter_chunks(
                        value, min_size=min_size, max_size=max_size
                    ):
                        await queue_text(value_id, chunk)
                        if is_punctuation_pause(chunk):
                            await flush_text()
                        await asyncio.sleep(pause_for_chunk(chunk))
                    await flush_text()

                nested = getattr(item, "blocks", None)
                if nested:
                    for k, child_raw in enumerate(nested):
                        await stream_any(
                            item_id, child_raw, local_suffix=f"{item_id}:{k}"
                        )

                if isinstance(value, list):
                    for k, child_raw in enumerate(value):
                        await stream_any(
                            item_id, child_raw, local_suffix=f"{item_id}:{k}"
                        )

        await stream_any(parent_id, block, suffix)
        await flush_text()

    def _effective(
        self,
        policy: OutputStreamPolicy,
        override: OutputStreaming | None,
    ) -> _EffectiveStreaming:
        if override is None:
            enabled = bool(policy.enabled)
            interval = float(policy.interval)
            chunk_size = int(policy.chunk_tokens)
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

    def _chunk_params(self, eff: _EffectiveStreaming) -> tuple[int, int]:
        max_size = _clamp_int(eff.chunk_size, self.MIN_CHUNK_SIZE, self.MAX_CHUNK_SIZE)
        min_size = max(self.MIN_CHUNK_SIZE, int(max_size * 0.4))
        return min_size, max_size
