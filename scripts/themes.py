"""Named theme definitions matching Textual's built-in themes.

Each theme maps to CSS variables used by the web client.
"""

THEMES = {
    "tokyo-night": {
        "font": '"SF Mono", "Cascadia Code", "Fira Code", "JetBrains Mono", "Consolas", "DejaVu Sans Mono", monospace',
        "bg": "#1A1B26",
        "surface": "#24283B",
        "text": "#a9b1d6",
        "accent": "#FF9E64",
        "secondary": "#7AA2F7",
        "primary": "#BB9AF7",
        "error": "#F7768E",
        "success": "#9ECE6A",
        "warning": "#E0AF68",
    },
    "dracula": {
        "font": '"SF Mono", "Cascadia Code", "Fira Code", "JetBrains Mono", "Consolas", "DejaVu Sans Mono", monospace',
        "bg": "#282a36",
        "surface": "#44475a",
        "text": "#f8f8f2",
        "accent": "#ffb86c",
        "secondary": "#8be9fd",
        "primary": "#bd93f9",
        "error": "#ff5555",
        "success": "#50fa7b",
        "warning": "#f1fa8c",
    },
}
