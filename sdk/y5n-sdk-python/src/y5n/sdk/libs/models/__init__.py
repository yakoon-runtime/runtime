"""Local JSON-protocol types — mirrors of y5n.base.contracts.

The SDK never imports from y5ncore-base. These types define the
SDK's understanding of the JSON protocol that the Host sends
over stdin/env (Context) and IPC (Call, Response, Register).
"""

from .call import Call
from .context import Context
from .flow import Flow
from .register import Register
from .request import Request
from .response import Response
from .session import Session

__all__ = [
    "Call",
    "Context",
    "Flow",
    "Register",
    "Request",
    "Response",
    "Session",
]
