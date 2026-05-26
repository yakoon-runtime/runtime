from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Capability:
    command_key: str
    controller_id: str
    score: float
    reason: str  # alias, tag, ai, etc.


class DiscoveryResult: ...


@dataclass(frozen=True, slots=True)
class Resolved(DiscoveryResult):
    capability: Capability


@dataclass(frozen=True, slots=True)
class Candidates(DiscoveryResult):
    items: list[Capability]


@dataclass(frozen=True, slots=True)
class NoMatch(DiscoveryResult):
    pass
