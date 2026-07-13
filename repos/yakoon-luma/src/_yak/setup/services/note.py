from __future__ import annotations

from typing import Protocol

from y5nstore.event.ports import OnDelete, OnGet, OnReplace

from ..data import NoteData
from ..models import Note, NoteLink
from .namespaces import note_key, note_namespace


class OnScan(Protocol):
    async def __call__(self, *, namespace) -> list: ...


class NoteService:

    def __init__(
        self,
        on_get: OnGet,
        on_replace: OnReplace,
        on_scan: OnScan,
        on_delete: OnDelete,
        on_next_id,
    ):
        self._on_get = on_get
        self._on_replace = on_replace
        self._on_scan = on_scan
        self._on_delete = on_delete
        self._on_next_id = on_next_id

    async def _all_notes(self) -> list[Note]:
        rows = await self._on_scan(namespace=note_namespace())
        result = []
        for r in rows:
            if r is None or r.key.id.startswith("link_"):
                continue
            data = NoteData.from_dict(r.require_object())
            result.append(Note(id=r.key.id, name=data.name, content=data.content))
        return result

    async def add_note(self, *, name: str, content: str) -> Note:
        for n in await self._all_notes():
            if n.name.lower() == name.lower():
                raise ValueError(f"Note '{name}' already exists.")
        next_id = await self._on_next_id(prefix="n")
        data = NoteData(name=name, content=content)
        await self._on_replace(key=note_key(str(next_id)), doc=data.to_dict())
        return Note(id=str(next_id), name=name, content=content)

    async def get_note(self, note_id: str) -> Note | None:
        row = await self._on_get(key=note_key(note_id))
        if row is None or row.data is None:
            return None
        data = NoteData.from_dict(row.require_object())
        return Note(id=note_id, name=data.name, content=data.content)

    async def find_note_by_name(self, name: str) -> Note | None:
        for n in await self._all_notes():
            if n.name.lower() == name.lower():
                return n
        return None

    async def update_note(self, *, note_id: str, name: str, content: str) -> Note:
        note = await self.get_note(note_id)
        if note is None:
            raise ValueError(f"Note '{note_id}' not found.")
        data = NoteData(name=name, content=content)
        await self._on_replace(key=note_key(note_id), doc=data.to_dict())
        return Note(id=note_id, name=name, content=content)

    async def delete_note(self, note_id: str) -> None:
        await self._on_delete(key=note_key(note_id))

    async def list_notes(self) -> list[Note]:
        return await self._all_notes()

    async def inbox(self) -> list[Note]:
        all_notes = await self._all_notes()
        linked_ids = {l.note_id for l in await self._all_links()}
        return [n for n in all_notes if n.id not in linked_ids]

    async def _all_links(self) -> list[NoteLink]:
        rows = await self._on_scan(namespace=note_namespace())
        links: list[NoteLink] = []
        for r in rows:
            if r is None or not r.key.id.startswith("link_"):
                continue
            obj = r.require_object() or {}
            if "box_id" in obj:
                links.append(NoteLink(id=r.key.id, note_id=obj.get("note_id", ""), box_id=obj.get("box_id", "")))
        return links

    async def link(self, *, note_id: str, box_id: str) -> NoteLink:
        for l in await self._all_links():
            if l.note_id == note_id and l.box_id == box_id:
                raise ValueError("Already linked.")
        next_id = await self._on_next_id(prefix="n")
        data = {"note_id": note_id, "box_id": box_id}
        await self._on_replace(key=note_key(f"link_{next_id}"), doc=data)
        return NoteLink(id=str(next_id), note_id=note_id, box_id=box_id)

    async def unlink(self, note_id: str, box_id: str) -> None:
        for l in await self._all_links():
            if l.note_id == note_id and l.box_id == box_id:
                await self._on_delete(key=note_key(l.id))
                return
        raise ValueError("Link not found.")

    async def links_for_box(self, box_id: str) -> list[NoteLink]:
        return [l for l in await self._all_links() if l.box_id == box_id]

    async def notes_for_box(self, box_id: str) -> list[Note]:
        note_ids = {l.note_id for l in await self._all_links() if l.box_id == box_id}
        all_notes = await self._all_notes()
        return [n for n in all_notes if n.id in note_ids]
