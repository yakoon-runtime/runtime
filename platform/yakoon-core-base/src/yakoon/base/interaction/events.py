class InputEvent:
    def __init__(self, text: str):
        self.text = text


class SubmitEvent:
    def __init__(self, values: dict):
        self.values = values
