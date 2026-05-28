import re

from .base import BasePolicy, ValidationError


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
            raise ValidationError(f"Mindestens {self.min_length} Zeichen.")

        if self.max_length is not None and len(raw) > self.max_length:
            raise ValidationError(f"Maximal {self.max_length} Zeichen.")

        if self.pattern:
            if not re.fullmatch(self.pattern, raw):
                raise ValidationError("Ungültiges Format.")

        return raw
