from pathlib import Path

from kivy.config import Config

Config.set("kivy", "exit_on_escape", "0")

from kivy.app import App  # noqa: E402
from kivy.core.text import LabelBase  # noqa: E402
from kivy.lang import Builder  # noqa: E402
from yakoon.kivy import (  # noqa: E402
    pages,  # noqa: F401
    widgets,  # noqa: F401
)
from yakoon.kivy.bootstrap.compose import compose_kivy_app  # noqa: E402


class YakoonKivyApp(App):
    title = "Yakoon"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._composition = None

    def build(self):
        self._load_environment()
        self._composition = compose_kivy_app()
        return self._composition.root

    def on_stop(self):
        # sauber runterfahren
        comp = self._composition
        if comp is not None:
            try:
                comp.runner.stop()
            except Exception:
                # UI shutdown soll nicht crashen
                pass

    def _load_environment(self):
        BASE = Path(__file__).resolve().parent
        self._load_fonts(BASE)
        self._load_layouts(BASE)

    def _load_fonts(self, base_folder: str):
        FONTS = base_folder / "assets" / "fonts"

        LabelBase.register(
            name="RobotoMono",
            fn_regular=str(FONTS / "RobotoMono-Regular.ttf"),
            fn_bold=str(FONTS / "RobotoMono-Bold.ttf"),
        )

        LabelBase.register(
            name="Icons",
            fn_regular=str(FONTS / "material-symbols-outlined-latin-300-normal.ttf"),
        )

    def _load_layouts(self, base_folder: str) -> None:
        LAYOUTS = base_folder / "layouts"

        def _sorted_kv(folder: Path) -> list[Path]:
            if not folder.exists():
                return []
            return sorted(p for p in folder.rglob("*.kv") if p.is_file())

        # 0) theme/base widgets first
        theme_kv = LAYOUTS / "theme.kv"
        if theme_kv.exists():
            Builder.load_file(str(theme_kv))

        # 1) widgets
        for kv in _sorted_kv(LAYOUTS / "widgets"):
            Builder.load_file(str(kv))

        # 2) pages
        for kv in _sorted_kv(LAYOUTS / "pages"):
            Builder.load_file(str(kv))

        # 3) app root
        app_kv = LAYOUTS / "app.kv"
        if app_kv.exists():
            Builder.load_file(str(app_kv))


if __name__ == "__main__":
    YakoonKivyApp().run()
