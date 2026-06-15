from __future__ import annotations

from dataclasses import dataclass

_FONT = '"SF Mono", "Cascadia Code", "Fira Code", "JetBrains Mono", "Consolas", "DejaVu Sans Mono", monospace'


@dataclass(frozen=True)
class Theme:
    name: str
    font: str = _FONT
    bg: str = "#1A1B26"
    surface: str = "#24283B"
    text: str = "#a9b1d6"
    accent: str = "#FF9E64"
    secondary: str = "#7AA2F7"
    primary: str = "#BB9AF7"
    error: str = "#F7768E"
    success: str = "#9ECE6A"
    warning: str = "#E0AF68"


class ThemeManager:
    """Central theme repository.

    All clients (Texture, Web, Tauri, …) resolve themes through this
    manager instead of carrying their own colour tables.
    """

    def __init__(self, themes: dict[str, Theme] | None = None):
        self._themes = dict(themes) if themes else {}

    def get(self, name: str) -> Theme | None:
        return self._themes.get(name)

    def list(self) -> list[str]:
        return list(self._themes)

    def as_css_vars(self, name: str) -> str:
        theme = self._themes.get(name)
        if not theme:
            return ""
        pairs = [
            f"    --{k}: {v};"
            for k, v in _css_map(theme).items()
        ]
        return ":root {\n" + "\n".join(pairs) + "\n}"


def _css_map(theme: Theme) -> dict[str, str]:
    return {
        "font": theme.font,
        "bg": theme.bg,
        "surface": theme.surface,
        "text": theme.text,
        "accent": theme.accent,
        "secondary": theme.secondary,
        "primary": theme.primary,
        "error": theme.error,
        "success": theme.success,
        "warning": theme.warning,
    }


TOKYO_NIGHT = Theme(
    name="tokyo-night",
    bg="#1A1B26",
    surface="#24283B",
    text="#a9b1d6",
    accent="#FF9E64",
    secondary="#7AA2F7",
    primary="#BB9AF7",
    error="#F7768E",
    success="#9ECE6A",
    warning="#E0AF68",
)

DRACULA = Theme(
    name="dracula",
    bg="#282a36",
    surface="#44475a",
    text="#f8f8f2",
    accent="#ffb86c",
    secondary="#8be9fd",
    primary="#bd93f9",
    error="#ff5555",
    success="#50fa7b",
    warning="#f1fa8c",
)

NORD = Theme(
    name="nord",
    bg="#2E3440",
    surface="#3B4252",
    text="#ECEFF4",
    accent="#88C0D0",
    secondary="#81A1C1",
    primary="#B48EAD",
    error="#BF616A",
    success="#A3BE8C",
    warning="#EBCB8B",
)

CATPPUCCIN = Theme(
    name="catppuccin",
    bg="#1e1e2e",
    surface="#313244",
    text="#cdd6f4",
    accent="#fab387",
    secondary="#89b4fa",
    primary="#cba6f7",
    error="#f38ba8",
    success="#a6e3a1",
    warning="#f9e2af",
)

SOLARIZED_DARK = Theme(
    name="solarized-dark",
    bg="#002b36",
    surface="#073642",
    text="#839496",
    accent="#b58900",
    secondary="#268bd2",
    primary="#6c71c4",
    error="#dc322f",
    success="#859900",
    warning="#cb4b16",
)

ONE_DARK = Theme(
    name="one-dark",
    bg="#282c34",
    surface="#353b45",
    text="#abb2bf",
    accent="#d19a66",
    secondary="#61afef",
    primary="#c678dd",
    error="#e06c75",
    success="#98c379",
    warning="#e5c07b",
)


CATPPUCCIN_MOCHA = Theme(
    name="catppuccin-mocha",
    bg="#1e1e2e",
    surface="#313244",
    text="#cdd6f4",
    accent="#fab387",
    secondary="#89b4fa",
    primary="#cba6f7",
    error="#f38ba8",
    success="#a6e3a1",
    warning="#f9e2af",
)

MONOKAI = Theme(
    name="monokai",
    bg="#272822",
    surface="#383830",
    text="#f8f8f2",
    accent="#fd971f",
    secondary="#66d9ef",
    primary="#ae81ff",
    error="#f92672",
    success="#a6e22e",
    warning="#e6db74",
)

ATOM_DARK = Theme(
    name="atom-dark",
    bg="#282c34",
    surface="#353b45",
    text="#abb2bf",
    accent="#d19a66",
    secondary="#61afef",
    primary="#c678dd",
    error="#e06c75",
    success="#98c379",
    warning="#e5c07b",
)


def default_themes() -> dict[str, Theme]:
    return {t.name: t for t in [TOKYO_NIGHT, DRACULA, NORD, CATPPUCCIN, CATPPUCCIN_MOCHA, SOLARIZED_DARK, ONE_DARK, MONOKAI, ATOM_DARK]}
