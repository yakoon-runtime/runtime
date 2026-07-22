import re

from .base import BasePolicy, ValidationError


class DatePolicy(BasePolicy):

    PATTERN = r"^\d{4}-\d{2}-\d{2}$"

    def coerce(self, raw: str):

        if not re.fullmatch(self.PATTERN, raw):
            raise ValidationError("Bitte Datum im Format YYYY-MM-DD eingeben.")

        return raw
