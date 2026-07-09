from y5n.api.nodes import Node

from .group.space import group as group_node
from .permission.space import permission as permission_node
from .user.space import user as user_node

# ----------------------------------
# GRANTS
# ----------------------------------

grant = Node(
    key="grants",
    anonymous=True,
    resolvable=False,
    navigable=True,
    contextual=True,
)

grant.mount(user_node)
grant.mount(group_node)
grant.mount(permission_node)
