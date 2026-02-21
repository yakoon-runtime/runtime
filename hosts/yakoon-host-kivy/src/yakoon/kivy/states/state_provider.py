from dataclasses import dataclass

from yakoon.base.runtime.session.session import Session
from yakoon.base.utils.format import format_ps1


@dataclass(frozen=True)
class UIState:
    prompt_prefix: str
    prompt_secret: bool


class UIStateProvider:

    def __init__(self, session: Session):
        self.session = session

    def __call__(self) -> UIState:
        prompt = format_ps1(self.session)
        secret = getattr(self.session, "prompt_secret", False)
        return UIState(prompt_prefix=prompt, prompt_secret=secret)
