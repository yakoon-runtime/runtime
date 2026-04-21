from yakoon.base.flow.dsl import write
from yakoon.base.projection.model import InlineText, TextBlock

from ...primitives.outcome import Outcome


def write_text(text: str) -> Outcome:
    return write(
        TextBlock(
            text=[InlineText("text", text)],
        )
    )
