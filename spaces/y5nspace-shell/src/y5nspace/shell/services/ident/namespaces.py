from y5n.api.naming import Namespace


class Namespaces:

    domain = "ident"
    space = "global"

    # ----------------------------------
    # NAMESPACES
    # ----------------------------------

    def user_namespace(self) -> Namespace:
        return Namespace(self.domain, "user", self.space)

    def group_namespace(self) -> Namespace:
        return Namespace(self.domain, "group", self.space)

    def join_namespace(self) -> Namespace:
        return Namespace(self.domain, "join", self.space)

    def permgrant_namespace(self) -> Namespace:
        return Namespace(self.domain, "permgrant", self.space)
