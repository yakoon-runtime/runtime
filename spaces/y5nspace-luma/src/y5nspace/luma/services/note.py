from __future__ import annotations

from ..models import Note, NoteLink
from .contracts import NoteService


class MemoryNoteService(NoteService):

    def __init__(self):
        self._notes: dict[str, Note] = {}
        self._links: dict[str, NoteLink] = {}
        self._next_note = 1
        self._next_link = 1

    def _new_note_id(self) -> str:
        n = self._next_note
        self._next_note += 1
        return f"n{n}"

    def _new_link_id(self) -> str:
        n = self._next_link
        self._next_link += 1
        return f"l{n}"

    async def add_note(self, *, name: str, content: str) -> Note:
        for n in self._notes.values():
            if n.name.lower() == name.lower():
                raise ValueError(f"Note '{name}' already exists.")
        note = Note(id=self._new_note_id(), name=name, content=content)
        self._notes[note.id] = note
        return note

    async def get_note(self, note_id: str) -> Note | None:
        return self._notes.get(note_id)

    async def find_note_by_name(self, name: str) -> Note | None:
        for n in self._notes.values():
            if n.name.lower() == name.lower():
                return n
        return None

    async def update_note(self, *, note_id: str, name: str, content: str) -> Note:
        note = self._notes.get(note_id)
        if note is None:
            raise ValueError(f"Note '{note_id}' not found.")
        note.name = name
        note.content = content
        return note

    async def delete_note(self, note_id: str) -> None:
        if note_id not in self._notes:
            raise ValueError(f"Note '{note_id}' not found.")
        del self._notes[note_id]
        self._links = {k: v for k, v in self._links.items() if v.note_id != note_id}

    async def list_notes(self) -> list[Note]:
        return list(self._notes.values())

    async def inbox(self) -> list[Note]:
        linked = {l.note_id for l in self._links.values()}
        return [n for n in self._notes.values() if n.id not in linked]

    async def link(self, *, note_id: str, box_id: str) -> NoteLink:
        for l in self._links.values():
            if l.note_id == note_id and l.box_id == box_id:
                raise ValueError("Already linked.")
        link = NoteLink(id=self._new_link_id(), note_id=note_id, box_id=box_id)
        self._links[link.id] = link
        return link

    async def unlink(self, note_id: str, box_id: str) -> None:
        for k, l in list(self._links.items()):
            if l.note_id == note_id and l.box_id == box_id:
                del self._links[k]
                return
        raise ValueError("Link not found.")

    async def links_for_box(self, box_id: str) -> list[NoteLink]:
        return [l for l in self._links.values() if l.box_id == box_id]

    async def notes_for_box(self, box_id: str) -> list[Note]:
        note_ids = {l.note_id for l in self._links.values() if l.box_id == box_id}
        return [n for n in self._notes.values() if n.id in note_ids]
