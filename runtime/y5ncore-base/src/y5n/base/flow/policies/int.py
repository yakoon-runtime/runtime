from .base import BasePolicy, ValidationError


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
            raise ValidationError("Bitte eine ganze Zahl eingeben.") from ValueError

        if self.min is not None and value < self.min:
            raise ValidationError(f"Mindestens {self.min}.")

        if self.max is not None and value > self.max:
            raise ValidationError(f"Maximal {self.max}.")

        return value
