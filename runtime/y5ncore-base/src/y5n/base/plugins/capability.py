from typing import Literal, TypeAlias

CapabilityMode: TypeAlias = Literal["default"]

CapabilitySelection: TypeAlias = dict[str, CapabilityMode | None]
