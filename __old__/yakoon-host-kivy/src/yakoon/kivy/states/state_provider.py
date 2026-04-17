from dataclasses import dataclass

from yakoon.platform.host.cli import format_ps1
from yakoon.platform.runtime.sessions.session import Session


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
