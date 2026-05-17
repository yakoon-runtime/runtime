from __future__ import annotations

from collections.abc import Callable
from typing import Any

# ----------------------------------
# HANDLER
# ----------------------------------

ResourceHandler = Callable[..., Any]
