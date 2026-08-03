"""Resource — re-exported from the API for component authors.

Components build a ``Resource`` via the factories (``text``, ``path``,
``traversable``) and return it from a resolve capability:

    from y5n.sdk import Resource

    def man() -> Resource:
        return Resource.traversable(files(__package__) / "resources" / "man.ydf")
"""

from y5n.runtime.api.resources import Resource

__all__ = ["Resource"]
