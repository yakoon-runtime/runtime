from yakoon.kivy.models.envelope import Envelope
from yakoon.kivy.runtime.demo.session import DemoSession


class DemoEngine:

    async def dispatch(self, session: DemoSession, text: str):
        text = (text or "").rstrip()

        if text.lower() in ("exit", "quit"):
            # optional: signal zum Schließen
            session.set_signal("exit_app")
            if session._io:
                await session._io.emit(Envelope(text="(system) bye"))
            return

        # Echo
        if session._io:
            session.prompt_prefix = "stefan@shell"
            await session._io.emit(Envelope(text=f"(output) {text}"))
