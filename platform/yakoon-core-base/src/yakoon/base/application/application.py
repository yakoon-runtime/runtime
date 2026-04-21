from collections.abc import Sequence

from yakoon.base.controllers import Controller


class Application:

    id: str = "unnamed"
    """Unique controller identifier used for command prefix resolution."""

    is_shell: bool = False
    """If True, the controller acts as a shell-like environment."""

    is_listed: bool = True
    """If False, the controller is hidden from listings (e.g. man/help, UI menus)."""

    is_activatable: bool = True
    """If False, the controller cannot be activated as an interactive context."""

    controllers: Sequence[type[Controller]]
    """Contains the controllers of this application."""
