from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import _yak.setup.python as luma_setup
import pytest
from y5n.api.naming import Key
from y5n.api.nodes import Node, NodeSpace
from y5n.base.nodes.request import Request
from y5n.base.runtime.input import Interaction
from y5n.runtime.runtime.sessions import SessionData


@dataclass
class FakeSession:
    data: SessionData = field(default_factory=SessionData)
    lang: str = "de"
    key: Key = field(
        default_factory=lambda: Key.from_parts("test", "session", "luma", "1")
    )
    _interaction: Interaction = Interaction.CLI
    _permissions: set[Any] = field(default_factory=set)

    def get_data(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

    def set_data(self, key: str, value: Any) -> None:
        self.data.set(key, value)

    def del_data(self, key: str, default: Any = None) -> Any:
        return self.data.pop(key, default)

    @property
    def permissions(self) -> set[Any]:
        return self._permissions

    @property
    def interaction(self) -> Interaction:
        return self._interaction

    @interaction.setter
    def interaction(self, value: Interaction) -> None:
        self._interaction = value

    def set_permissions(self, permset: Any) -> None:
        self._permissions = permset

    def set_identity(self, user_key: Any, user_name: str | None = None) -> None:
        pass

    def get_identity(self) -> Any:
        return None

    def get_identity_name(self) -> str | None:
        return None


@dataclass
class FakePorts:
    _store: dict = field(default_factory=dict)

    def provide(self, port: Any, impl: Any) -> None:
        self._store[port] = impl

    def get(self, port: Any) -> Any:
        return self._store.get(port)


@pytest.fixture
async def fresh_space():
    session = FakeSession()
    root = Node(key="luma")
    space = NodeSpace(
        path=root.path,
        request=Request(command="test", tokens=[], payload=None, lang="de"),
        session=session,
        ports=FakePorts(),
        ports_from=None,
    )
    await luma_setup.run(space)
    session.set_data("luma.current_world", None)
    session.set_data("luma.current_box", None)
    return session, space
