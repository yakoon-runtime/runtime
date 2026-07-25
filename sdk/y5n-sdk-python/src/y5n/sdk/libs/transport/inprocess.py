"""In-process transport — calls the Runtime Bus directly.

Only available when running inside Yakoon's Python process.
"""

from typing import Any


async def invoke(call_dict: dict[str, Any]) -> dict[str, Any]:
    from y5n.runtime.api.runtime.context import Call as _RuntimeCall
    from y5n.runtime.api.runtime.context import invoke as _runtime_invoke

    rc = _RuntimeCall(
        port=call_dict.get("port", ""),
        method=call_dict.get("method", ""),
        args=call_dict.get("args", {}),
        caller_path=call_dict.get("caller_path", ""),
        caller_session_key=call_dict.get("caller_session_key", ""),
    )
    rr = await _runtime_invoke(rc)
    return {"result": rr.result, "error": rr.error}


def register(
    reg_dict: dict[str, Any], methods_dict: dict[str, Any] | None = None
) -> None:
    import uuid

    from y5n.runtime.api.runtime.bus import get_bus
    from y5n.runtime.api.runtime.messages import Placement, RegisterProvider

    placement = {
        "self": Placement.SELF,
        "parent": Placement.PARENT,
        "root": Placement.ROOT,
    }.get(reg_dict.get("placement", "self"), Placement.SELF)

    name = reg_dict.get("name", "")
    get_bus().dispatch(
        RegisterProvider(
            provider_id=f"provider:{uuid.uuid4().hex}",
            exports={name: reg_dict.get("methods", [])},
            service=methods_dict or {},
            placement=placement,
            caller_path=reg_dict.get("caller_path", ""),
        )
    )
