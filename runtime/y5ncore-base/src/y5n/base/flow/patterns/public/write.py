from y5n.base.flow.dsl import write
from y5n.base.projection.model import InlineText, TextBlock

from ...primitives.outcome import Outcome


def write_text(text: str) -> Outcome:
    return write(
        TextBlock(
            text=[InlineText("text", text)],
        )
    )
