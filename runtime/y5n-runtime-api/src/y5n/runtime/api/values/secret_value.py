from dataclasses import dataclass


@dataclass(frozen=True)
class SecretValue:
    value: str

    def reveal(self) -> str:
        return self.value

    def __str__(self) -> str:
        return "******"

    def __repr__(self) -> str:
        return "SecretValue(******)"
