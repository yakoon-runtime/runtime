from dataclasses import dataclass


@dataclass
class EngineSettings:

    # Feature Toggles
    enable_batch: bool = True
    """Allows multiple commands in one input via 'batch:' prefix."""

    enable_webapi: bool = True
    """Enables the FastAPI-based web interface."""

    enable_telnet: bool = True
    """Enables the Telnet server interface."""
