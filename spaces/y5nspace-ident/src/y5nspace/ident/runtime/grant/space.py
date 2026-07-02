from y5n.api.invocations import Invocation, Param
from y5n.api.nodes import Node

from .grant_add import run as grant_add
from .grant_group import run as grant_group
from .grant_perm import run as grant_perm
from .grant_remove import run as grant_remove
from .grant_user import run as grant_user
from .setup import setup

# ----------------------------------
# MEMBERSHIP
# ----------------------------------

grant = Node(
    key="grants",
    anonymous=True,
    resolvable=True,
    navigable=True,
    contextual=True,
    setup=setup,
    run=grant_user,
    invocations=[
        Invocation(
            action="user",
            params=[Param(key="username", required=True, positional=True)],
        ),
    ],
)


grant.add(
    Node(
        key="add",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=grant_add,
        invocations=[
            Invocation(
                params=[
                    Param(key="type", required=True, positional=True),
                    Param(key="name", required=True, positional=True),
                    Param(key="permission", required=True, positional=True),
                    Param(key="bits"),
                    Param(key="deny"),
                ],
            ),
        ],
    ),
)

grant.add(
    Node(
        key="remove",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=grant_remove,
        invocations=[
            Invocation(
                params=[
                    Param(key="type", required=True, positional=True),
                    Param(key="name", required=True, positional=True),
                    Param(key="permission", required=True, positional=True),
                ]
            ),
        ],
    ),
)


grant.add(
    Node(
        key="user",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=grant_user,
        invocations=[
            Invocation(
                action="user",
                params=[Param(key="username", required=True, positional=True)],
            ),
        ],
    ),
)

grant.add(
    Node(
        key="group",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=grant_group,
        invocations=[
            Invocation(params=[Param(key="groupname", required=True, positional=True)])
        ],
    ),
)

grant.add(
    Node(
        key="permission",
        anonymous=True,
        resolvable=True,
        navigable=False,
        run=grant_perm,
        invocations=[
            Invocation(params=[Param(key="permission", required=True, positional=True)])
        ],
    ),
)
