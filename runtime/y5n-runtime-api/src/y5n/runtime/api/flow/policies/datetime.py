import re

from .base import BasePolicy, ValidationError


class DateTimePolicy(BasePolicy):

    PATTERN = r"^\d{4}-\d{2}-\d{2}T([01]\d|2[0-3]):([0-5]\d)$"

    def coerce(self, raw: str):

        if re.fullmatch(self.PATTERN, raw):
            return raw

        raise ValidationError(
            "Bitte Datum und Uhrzeit im Format YYYY-MM-DDTHH:MM eingeben."
        )
