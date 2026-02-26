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

    MIN_DEFAULT = 12
    MAX_DEFAULT = 48

    MIN_AGGRESSIV = 32
    MAX_AGGRESSIV = 96

    MIN_CHUNK_SIZE = MIN_DEFAULT
    MAX_CHUNK_SIZE = MAX_DEFAULT

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

        interval = float(eff.interval)

        # stable view id for whole stream
        vid = eff.id or view.id or f"v:{id(view)}"

        async def emit_patch(ops, *, final: bool = False):
            await session.emit(
                replace(
                    view,
                    id=vid,
                    mode="patch",
                    patch=PatchSpec(ops=ops, final=final),
                )
            )
            await asyncio.sleep(0)

        async def natural_pause(chunk):
            pause = interval * random.uniform(0.85, 1.15)
            if chunk and chunk.strip() and chunk.strip()[-1] in ".:!?":
                pause *= 1.25

            await asyncio.sleep(pause)

        def ensure_id(b: Any, idx: int) -> Any:
            bid = getattr(b, "id", None)
            if bid:
                idx = bid
            #    return b
            # stable enough; bound to view id + index
            return replace(b, id=f"{vid}:b{idx}")

        def ensure_item_id(item: Any, list_id: str, j: int) -> Any:
            iid = getattr(item, "id", None)
            if iid:
                return item
            return replace(item, id=f"{list_id}:i{j}")

        def can_merge_text(active_style: Any, b: Any) -> bool:
            return (
                getattr(b, "type", None) == "text"
                and isinstance(getattr(b, "text", None), str)
                and getattr(b, "style", None) == active_style
            )

        def iter_chunks(text: str) -> Iterator[str]:
            """
            Natural-feeling chunk generator.

            - Prefers word boundaries.
            - Ensures chunks are between min_size and max_size (approx).
            - Splits oversized tokens safely.
            """
            tokens = re.findall(r"\S+|\s+", text)
            min_size = self.MIN_CHUNK_SIZE
            max_size = self.MAX_CHUNK_SIZE
            buffer = ""

            if not text:
                return

            tokens = re.findall(r"\S+|\s+", text)

            buffer = ""

            for token in tokens:
                # If single token is extremely long -> hard split
                if len(token) > max_size:
                    # flush existing buffer first
                    if buffer:
                        yield buffer
                        buffer = ""

                    for i in range(0, len(token), max_size):
                        yield token[i : i + max_size]
                    continue

                # If adding token would overflow max_size → emit buffer
                if buffer and len(buffer) + len(token) > max_size:
                    yield buffer
                    buffer = token
                    continue

                buffer += token

                # If buffer reached minimum natural size → emit
                if len(buffer) >= min_size:
                    yield buffer
                    buffer = ""

            if buffer:
                yield buffer

        # reset stream in host container
        await emit_patch([PatchReset()], final=False)

        active_text_id: str | None = None
        active_style: Any = None

        for idx, block in enumerate(blocks):
            block = ensure_id(block, idx)
            btype = getattr(block, "type", None)
            text = getattr(block, "text", None)

            # LIST -> stream container first, then append_child for each item
            if btype == "list":
                # open empty list container in host
                empty_list = replace(block, items=[])
                await emit_patch([PatchAppendBlock(block=empty_list)], final=False)

                list_id = getattr(empty_list, "id", None) or getattr(block, "id", "")

                items = list(getattr(block, "items", None) or [])
                for j, item in enumerate(items):
                    # 1) append empty item first
                    item = ensure_item_id(item, list_id, j)

                    head = getattr(item, "head", "")
                    empty_item = replace(item, head="" if isinstance(head, str) else [])

                    await emit_patch(
                        [PatchAppendChild(parent_id=list_id, block=empty_item)],
                        final=False,
                    )

                    # 2) stream head text into alias target "<item_id>.head"
                    item_id = getattr(empty_item, "id", None)
                    head_id = f"{item_id}.head"

                    # Only stream plain-string heads for now (inline-head streaming later)
                    if isinstance(head, str) and head:
                        for chunk in iter_chunks(head):
                            await emit_patch(
                                [PatchAppendText(block_id=head_id, text=chunk)],
                                final=False,
                            )
                            await natural_pause(chunk)

                    # 3) nested blocks remain snapshot for now
                    nested = getattr(item, "blocks", None)
                    if nested:
                        for child in nested:
                            child = ensure_id(child, f"{item_id}:{id(child)}")
                            await emit_patch(
                                [PatchAppendChild(parent_id=item_id, block=child)],
                                final=False,
                            )

                active_text_id = None
                active_style = None
                continue

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

                full = prefix + text
                tid = active_text_id or getattr(block, "id", "")
                for chunk in iter_chunks(full):
                    await emit_patch(
                        [PatchAppendText(block_id=tid, text=chunk)], final=False
                    )
                    await natural_pause(chunk)

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
