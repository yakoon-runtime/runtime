from typing import Any


class BaseError(Exception):

    # stable semantic key
    CODE: str

    # support-visible id
    NUMBER: int | None = None

    # app/runtime namespace
    app_id: str = "system"

    # structured runtime data
    data: dict[str, Any]

    # developer/runtime explanation
    dev_hint: str | None = None

    def __init__(
        self,
        *,
        app_id: str,
        data: dict[str, Any] | None,
        dev_hint: str | None,
    ):
        self.app_id = app_id
        if not self.app_id:
            raise ValueError("Parameter app_id must not be None")

        self.number = self.NUMBER
        if self.number is None:
            raise ValueError("Parameter number must not be None")

        self.code = self.CODE
        if not self.code:
            raise ValueError("Parameter code must not be None")

        self.data = data or {}
        self.dev_hint = dev_hint

    @property
    def support_id(self) -> str:

        if self.number is None:
            return f"({self.app_id})"

        return f"({self.app_id}:{self.number})"

    @property
    def message(self) -> dict[str, Any]:

        return {
            "code": self.CODE,
            "data": self.data,
        }


# ----------------------------------------
# FORMATTER
# ----------------------------------------


def format_error(error: BaseError, message: str, debug: bool = False) -> str:
    if not debug:
        return message
    return f"{error.support_id} " f"{message}"


# ----------------------------------------
# DOMAIN ERROR
# ----------------------------------------


class DomainError(BaseError):
    pass
