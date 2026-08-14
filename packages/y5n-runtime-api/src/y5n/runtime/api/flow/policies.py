"""Input validation policies.

A policy coerces a raw input string into a typed value and raises
``ValidationError`` with a human-readable message on failure. The ``required``
flag rejects empty input; an empty optional input coerces to ``None``.
"""

from __future__ import annotations

import re
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
            raise ValidationError("Value is required.")

        if raw_str == "":
            return None

        return self.coerce(raw_str)

    @abstractmethod
    def coerce(self, raw: str) -> Any:
        pass


class BoolPolicy(BasePolicy):

    def __init__(
        self,
        *,
        true_values: set[str],
        false_values: set[str],
    ):
        super().__init__()

        self.true_values = {v.lower() for v in true_values}
        self.false_values = {v.lower() for v in false_values}

        if self.true_values & self.false_values:
            raise ValueError("true_values and false_values overlap")

    def coerce(self, raw: str):

        value = raw.lower()
        if value in self.true_values:
            return True

        if value in self.false_values:
            return False

        allowed = sorted(self.true_values | self.false_values)

        raise ValidationError("Allowed values: " + ", ".join(allowed))


class IntPolicy(BasePolicy):

    def __init__(
        self,
        *,
        min: int | None = None,
        max: int | None = None,
    ):
        super().__init__()

        self.min = min
        self.max = max

    def coerce(self, raw: str):

        try:
            value = int(raw)
        except ValueError:
            raise ValidationError("Please enter an integer.") from ValueError

        if self.min is not None and value < self.min:
            raise ValidationError(f"Must be at least {self.min}.")

        if self.max is not None and value > self.max:
            raise ValidationError(f"Must be at most {self.max}.")

        return value


class FloatPolicy(BasePolicy):

    def __init__(
        self,
        *,
        min: float | None = None,
        max: float | None = None,
    ):
        super().__init__()

        self.min = min
        self.max = max

    def coerce(self, raw: str):

        try:
            value = float(raw)
        except ValueError:
            raise ValidationError("Please enter a number.") from ValueError

        if self.min is not None and value < self.min:
            raise ValidationError(f"Must be at least {self.min}.")

        if self.max is not None and value > self.max:
            raise ValidationError(f"Must be at most {self.max}.")

        return value


class StringPolicy(BasePolicy):

    def __init__(
        self,
        *,
        min_length: int | None = None,
        max_length: int | None = None,
        pattern: str | None = None,
    ):
        super().__init__()

        self.min_length = min_length
        self.max_length = max_length
        self.pattern = pattern

    def coerce(self, raw: str):

        if self.min_length is not None and len(raw) < self.min_length:
            raise ValidationError(f"Must be at least {self.min_length} characters.")

        if self.max_length is not None and len(raw) > self.max_length:
            raise ValidationError(f"Must be at most {self.max_length} characters.")

        if self.pattern:
            if not re.fullmatch(self.pattern, raw):
                raise ValidationError("Invalid format.")

        return raw


class EmailPolicy(StringPolicy):

    def __init__(self):

        super().__init__(
            pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
        )

    def coerce(self, raw: str):

        try:
            return super().coerce(raw)
        except ValidationError:
            raise ValidationError(
                "Please enter a valid email address."
            ) from ValidationError


class DateTimePolicy(BasePolicy):

    PATTERN = r"^\d{4}-\d{2}-\d{2}T([01]\d|2[0-3]):([0-5]\d)$"

    def coerce(self, raw: str):

        if re.fullmatch(self.PATTERN, raw):
            return raw

        raise ValidationError(
            "Please enter a date and time in the format YYYY-MM-DDTHH:MM."
        )


class TimePolicy(BasePolicy):

    PATTERN = r"^([01]\d|2[0-3]):([0-5]\d)$"

    def coerce(self, raw: str):

        if re.fullmatch(self.PATTERN, raw):
            return raw

        raise ValidationError("Please enter a time in the format HH:MM.")


class DatePolicy(BasePolicy):

    PATTERN = r"^\d{4}-\d{2}-\d{2}$"

    def coerce(self, raw: str):

        if not re.fullmatch(self.PATTERN, raw):
            raise ValidationError("Please enter a date in the format YYYY-MM-DD.")

        return raw


__all__ = [
    "ValidationError",
    "BasePolicy",
    "BoolPolicy",
    "IntPolicy",
    "FloatPolicy",
    "StringPolicy",
    "EmailPolicy",
    "DateTimePolicy",
    "TimePolicy",
    "DatePolicy",
]
