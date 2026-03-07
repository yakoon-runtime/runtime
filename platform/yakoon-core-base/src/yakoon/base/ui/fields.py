from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class SelectOption:
    value: str
    label: str


class FieldType(StrEnum):
    STRING = "string"
    INT = "int"
    FLOAT = "float"
    BOOL = "bool"
    DATE = "date"
    SELECT = "select"


@dataclass(frozen=True)
class SecretValue:
    value: str

    def reveal(self) -> str:
        return self.value

    def __str__(self) -> str:
        return "******"

    def __repr__(self) -> str:
        return "SecretValue(******)"
