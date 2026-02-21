import os
from dataclasses import dataclass


@dataclass
class BaseSettings:

    dev_mode = os.getenv("DEV_MODE", "false").lower() in ("1", "true", "yes")

    # Debugging & Logging
    debug: bool = True
    """If True, enables verbose output and developer diagnostics."""
