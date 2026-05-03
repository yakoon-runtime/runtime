from yakoon.base.application import Application
from yakoon.base.plugins import ModulePorts
from yakoon.base.plugins.ports import OnAuthenticate

from .controllers import BaseController
from .services import AuthenticationService


class IdentityApp(Application):

    id: str = "ident-app"
    name = "ident"

    controllers = (BaseController,)

    auth: AuthenticationService

    def on_initialize(self, ports: ModulePorts) -> None:
        self.auth = AuthenticationService()
        ports.on_publish(OnAuthenticate, self.auth.authenticate)
