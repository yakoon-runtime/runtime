from __future__ import annotations

from yakoon.kivy.models.mount import RenderMount


class ChatRenderService:
    """
    Host-seitig (Kivy). Macht aus ViewSpec -> Mount-Anweisung.
    """

    def render(self, view) -> list[RenderMount]:
        msg = getattr(view, "message", None)
        if msg is None:
            return []

        vid = getattr(view, "id", None)
        mode = getattr(view, "mode", None)

        # Stream-Flag: bevorzugt MessageSpec.stream, fallback auf view.meta["stream"]
        stream = getattr(msg, "stream", None)
        if stream is None:
            meta = getattr(view, "meta", None) or {}
            stream = meta.get("stream")

        is_final = stream == "final"

        # Heuristik:
        # - replace + nicht-final => live
        # - final oder append => history
        if mode == "replace" and vid and not is_final:
            return [RenderMount("live", "set_live", vid, view)]

        # final: erst live löschen (falls es dasselbe vid ist), dann in history
        if is_final and vid:
            return [
                RenderMount("live", "clear_live", vid, None),
                RenderMount(
                    "history",
                    "append_history",
                    vid,
                    {"viewclass": "ChatMessageRow", "vid": vid, "view": view},
                ),
            ]

        # normal append (nicht stream)
        return [
            RenderMount(
                "history",
                "append_history",
                vid,
                {"viewclass": "ChatMessageRow", "vid": vid, "view": view},
            ),
        ]
