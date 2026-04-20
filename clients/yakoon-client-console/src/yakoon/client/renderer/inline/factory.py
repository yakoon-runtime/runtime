from .base import BaseInlineRenderer, _get
from .break_ import BreakInlineRenderer
from .cmd import CmdInlineRenderer
from .code import CodeInlineRenderer
from .em import EmInlineRenderer
from .link import LinkInlineRenderer
from .mark import MarkInlineRenderer
from .select import SelectInlineRenderer
from .strong import StrongInlineRenderer
from .text import TextInlineRenderer
from .underline import UnderlineInlineRenderer
from .unknow import UnknownInlineRenderer


class InlineRendererFactory:

    def __init__(self):
        self._types = {
            "text": TextInlineRenderer,
            "code": CodeInlineRenderer,
            "link": LinkInlineRenderer,
            "cmd": CmdInlineRenderer,
            "strong": StrongInlineRenderer,
            "em": EmInlineRenderer,
            "underline": UnderlineInlineRenderer,
            "mark": MarkInlineRenderer,
            "select": SelectInlineRenderer,
            "break": BreakInlineRenderer,
        }

    def create(self, node) -> BaseInlineRenderer:
        t = _get(node, "type")
        cls = self._types.get(t or "")
        if not cls:
            return UnknownInlineRenderer(node, f"Unknown inline: {t}")
        return cls(node)
