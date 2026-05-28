from abc import ABC, abstractmethod
from typing import Any


class ValidationError(Exception):
    pass


class BasePolicy(ABC):

    def __init__(
        self,
        *,
        required: bool = False,
    ):
        self.required = required

    def validate(self, raw):

        raw_str = "" if raw is None else str(raw).strip()

        if self.required and raw_str == "":
            raise ValidationError("Wert ist erforderlich.")

        if raw_str == "":
            return None

        return self.coerce(raw_str)

    @abstractmethod
    def coerce(self, raw: str) -> Any:
        pass
