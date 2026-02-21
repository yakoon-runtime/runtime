from dataclasses import dataclass


@dataclass
class CmdSetCategoriesSetting:

    account: str = "account"
    system: str = "system"
    admin: str = "admin"
