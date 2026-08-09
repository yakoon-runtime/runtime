from dataclasses import dataclass


@dataclass
class LoggingSettings:

    log_errors: bool = True
    """Logs unexpected exceptions raised during execution."""

    log_warnings: bool = True
    """Logs warnings raised during execution."""

    log_to_file: bool = False
    """If True, logs will also be written to a file."""

    log_dir: str = "~/.local/state/yakoon/logs"
    """Directory for log files. Supports ~ expansion."""
