from .base import BasePolicy, ValidationError


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
            raise ValidationError("Bitte eine Zahl eingeben.") from ValidationError

        if self.min is not None and value < self.min:
            raise ValidationError(f"Mindestens {self.min}.")

        if self.max is not None and value > self.max:
            raise ValidationError(f"Maximal {self.max}.")

        return value
