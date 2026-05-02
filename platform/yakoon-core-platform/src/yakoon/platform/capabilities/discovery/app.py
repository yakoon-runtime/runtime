from yakoon.base.application import Application

from .controllers import DiscoveryController


class DiscoveryApplication(Application):

    id: str = "discovery-app"
    name: str = "discover"

    controllers = (DiscoveryController,)
