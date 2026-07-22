from __future__ import annotations

import difflib


class GuidanceService:

    def suggest(
        self,
        *,
        value: str,
        choices: list[str],
        limit: int = 3,
        cutoff: float = 0.5,
    ) -> list[str]:

        if not value:
            return []

        return difflib.get_close_matches(
            value,
            choices,
            n=limit,
            cutoff=cutoff,
        )
