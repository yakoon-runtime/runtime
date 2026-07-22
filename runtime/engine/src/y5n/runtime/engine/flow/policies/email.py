from .string import StringPolicy, ValidationError


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
                "Bitte eine gültige E-Mail-Adresse eingeben."
            ) from ValidationError
