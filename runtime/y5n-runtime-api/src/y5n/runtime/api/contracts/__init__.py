"""Language-neutral contracts between Runtime and Host.

These types define the JSON protocol shared across all language
SDKs (Python, .NET, Go, etc.). Every SDK consumes this contract
and wraps it into language-native objects.
"""

from .call import Call
from .context import Context
from .register import Register
from .response import Response

__all__ = ["Call", "Context", "Register", "Response"]
