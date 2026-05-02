from yakoon.base.application import Application

from .controllers import BaseController


class IdentityApp(Application):

    id: str = "identity-app"
    name = "ident"

    controllers = (BaseController,)
