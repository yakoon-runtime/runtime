from yakoon.base.application import Application

from .controllers import DiscoveryController


class DiscoveryApplication(Application):

    id: str = "discovery"

    controllers = (DiscoveryController,)
