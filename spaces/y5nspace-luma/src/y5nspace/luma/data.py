from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class WorldData:
    CURRENT_VERSION = 1
    name: str
    description: str = ""
    entry_box_id: str | None = None
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {"name": self.name, "description": self.description, "entry_box_id": self.entry_box_id, "_v": self._v}

    @classmethod
    def from_dict(cls, d: dict) -> WorldData:
        d = dict(d or {})
        return cls(name=d["name"], description=d.get("description", ""), entry_box_id=d.get("entry_box_id"), _v=d.get("_v", 0))


@dataclass
class BoxData:
    CURRENT_VERSION = 1
    world_id: str
    parent_id: str | None
    name: str
    description: str = ""
    portable: bool = False
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {"world_id": self.world_id, "parent_id": self.parent_id, "name": self.name, "description": self.description, "portable": self.portable, "_v": self._v}

    @classmethod
    def from_dict(cls, d: dict) -> BoxData:
        d = dict(d or {})
        return cls(world_id=d["world_id"], parent_id=d.get("parent_id"), name=d["name"], description=d.get("description", ""), portable=d.get("portable", False), _v=d.get("_v", 0))


@dataclass
class ExitData:
    CURRENT_VERSION = 1
    world_id: str
    source_box_id: str
    target_box_id: str
    name: str = ""
    description: str = ""
    direction: str = ""
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {"world_id": self.world_id, "source_box_id": self.source_box_id, "target_box_id": self.target_box_id, "name": self.name, "description": self.description, "direction": self.direction, "_v": self._v}

    @classmethod
    def from_dict(cls, d: dict) -> ExitData:
        d = dict(d or {})
        return cls(world_id=d["world_id"], source_box_id=d["source_box_id"], target_box_id=d["target_box_id"], name=d.get("name", ""), description=d.get("description", ""), direction=d.get("direction", ""), _v=d.get("_v", 0))


@dataclass
class NoteData:
    CURRENT_VERSION = 1
    name: str
    content: str = ""
    _v: int = field(default=CURRENT_VERSION)

    def to_dict(self) -> dict:
        return {"name": self.name, "content": self.content, "_v": self._v}

    @classmethod
    def from_dict(cls, d: dict) -> NoteData:
        d = dict(d or {})
        return cls(name=d["name"], content=d.get("content", ""), _v=d.get("_v", 0))
