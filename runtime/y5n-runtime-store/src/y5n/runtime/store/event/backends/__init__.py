from .memory import MemoryBackend

__all__ = [
    "MemoryBackend",
]


def __getattr__(name: str):
    if name == "PostgresBackend":
        from .postgres import PostgresBackend

        return PostgresBackend
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
