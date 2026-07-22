from dataclasses import dataclass


@dataclass
class Note:
    id: str
    name: str
    content: str = ""


@dataclass
class NoteLink:
    id: str
    note_id: str
    box_id: str
