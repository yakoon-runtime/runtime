"""Language-neutral contracts between Runtime and Host.

These types define the JSON protocol shared across all language
SDKs (Python, .NET, Go, etc.). Every SDK consumes this contract
and wraps it into language-native objects.
"""

from .context import Context

__all__ = ["Context"]
