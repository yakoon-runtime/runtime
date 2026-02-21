from yakoon.platform.settings.base import BaseSettings
from yakoon.platform.settings.cmdsets import CmdSetCategoriesSetting
from yakoon.platform.settings.engine import EngineSettings
from yakoon.platform.settings.logging import LoggingSettings
from yakoon.platform.settings.network import NetSettings
from yakoon.platform.settings.plugings.ai import AISettings


class SaasSettings:

    ai = AISettings()
    base = BaseSettings()
    engine = EngineSettings()
    network = NetSettings()
    logging = LoggingSettings()

    cmdsets = CmdSetCategoriesSetting()


settings = SaasSettings()
