from dataclasses import dataclass


@dataclass
class LoggingSettings:

    log_commands: bool = True
    """Logs every command issued by a session."""

    log_audits: bool = True
    """Logs audits"""

    log_errors: bool = True
    """Logs unexpected exceptions raised during execution."""

    log_warnings: bool = True
    """Logs warnings raised during execution."""

    log_security: bool = True
    """Logs access denials (e.g. PermissionError, has_perm=False)."""

    log_to_file: bool = False
    """If True, logs will also be written to a file."""

    log_dir: str = "~/.local/state/yakoon/logs"
    """Directory for log files. Supports ~ expansion."""
