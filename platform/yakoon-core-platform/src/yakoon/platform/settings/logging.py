from dataclasses import dataclass


@dataclass
class LoggingSettings:

    log_commands: bool = True
    """Logs every command issued by a session."""

    log_errors: bool = True
    """Logs unexpected exceptions raised during execution."""

    log_permission_denied: bool = True
    """Logs access denials (e.g. PermissionError, has_perm=False)."""

    log_to_file: bool = False
    """If True, logs will also be written to a file."""

    log_file_path: str = "yakoon.log"
    """Path to the log file if log_to_file is enabled."""
