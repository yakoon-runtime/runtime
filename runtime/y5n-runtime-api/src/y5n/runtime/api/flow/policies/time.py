import re

from .base import BasePolicy, ValidationError


class TimePolicy(BasePolicy):

    PATTERN = r"^([01]\d|2[0-3]):([0-5]\d)$"

    def coerce(self, raw: str):

        if re.fullmatch(self.PATTERN, raw):
            return raw

        raise ValidationError("Bitte Zeit im Format HH:MM eingeben.")
