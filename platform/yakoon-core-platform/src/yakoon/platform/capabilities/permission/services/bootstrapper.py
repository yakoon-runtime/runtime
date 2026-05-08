from yakoon.platform.capabilities.permission import PermissionSet
from yakoon.platform.runtime.sessions import Session


class PermissionBootstrapper:

    def __init__(self, permissions: PermissionSet):
        self.permissions = permissions

    def apply(self, session: Session):
        session.set_permissions(self.permissions.clone())
