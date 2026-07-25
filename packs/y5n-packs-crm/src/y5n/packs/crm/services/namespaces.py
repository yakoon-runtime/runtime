from y5n.runtime.api.naming import Namespace


class Namespaces:
    domain = "crm"
    space = "global"

    def contact_namespace(self) -> Namespace:
        return Namespace(self.domain, "contact", self.space)
