from yakoon.base.application import Application

from .controllers import AuthCoreController


class AuthApplication(Application):

    id: str = "auth-app"

    controllers = (AuthCoreController,)
