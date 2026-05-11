from __future__ import annotations

from .text_de import command_not_found_de
from .text_en import command_not_found_en

MESSAGES = {
    "en": {
        "command_not_found": command_not_found_en,
        "permission_denied": "Permission denied",
    },
    "de": {
        "command_not_found": command_not_found_de,
        # "command_not_found": 'Befehl "{command}" wurde nicht gefunden',
        "permission_denied": "Zugriff verweigert",
    },
}
