from y5n.base.application import Application

from .controllers import DiscoveryComposer


class DiscoveryApplication(Application):

    id: str = "discovery-app"
    name: str = "discover"

    composers = (DiscoveryComposer,)
