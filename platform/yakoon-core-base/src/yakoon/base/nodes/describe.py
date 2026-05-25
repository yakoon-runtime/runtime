from dataclasses import dataclass


@dataclass(slots=True, frozen=True)
class NodeDescription:

    key: str
    name: str | None

    root: str
    parent: str | None

    kind: str
    scope: str
    visibility: str

    navigable: bool
    resolvable: bool
    listed: bool

    anonymous: bool
