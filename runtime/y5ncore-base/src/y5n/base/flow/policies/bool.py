from .base import BasePolicy, ValidationError


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

        raise ValidationError("Erlaubte Werte: " + ", ".join(allowed))
