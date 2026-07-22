from dataclasses import dataclass
from enum import StrEnum


class StreamEventType(StrEnum):
    TEXT = "text"
    FINISH = "finish"


@dataclass(slots=True)
class StreamEvent:
    type: StreamEventType


@dataclass(slots=True)
class TextEvent(StreamEvent):
    node: str
    key: str
    text: str
    pos: int = 0


@dataclass(slots=True)
class FinishEvent(StreamEvent):
    node: str
