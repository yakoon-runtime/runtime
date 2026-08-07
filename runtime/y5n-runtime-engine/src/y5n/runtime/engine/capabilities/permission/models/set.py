from __future__ import annotations

from y5n.runtime.api.permissions import PermBits, Permission


class PermissionSet:
    """
    Holds effective permissions for a session/account.

    Policy:
      - A grant on a path applies to that path and all its descendants
        (segment-based inheritance along the runtime path hierarchy).
      - The most specific matching grant decides.
      - On the same level: allows accumulate (union), denies subtract
        (deny wins over allow for the denied bits).
      - Traversal: READ on a container is granted when a grant lies
        underneath it (the path to your rights is traversable), as long
        as a deny does not remove `r` on the path itself.
    """

    def __init__(self) -> None:
        self._allow: dict[str, Permission] = {}
        self._deny: dict[str, Permission] = {}

    def __iter__(self):
        yield from self._allow.values()
        yield from self._deny.values()

    def add(self, perm: Permission) -> None:
        target = self._deny if perm.deny else self._allow
        existing = target.get(perm.path)

        if not existing:
            target[perm.path] = perm
            return

        # merge bits (same deny/allow bucket)
        target[perm.path] = Permission(
            path=perm.path,
            bits=existing.bits.union(perm.bits),
            deny=perm.deny,
        )

    def merge(self, other: PermissionSet) -> None:
        for p in other:
            self.add(p)

    def check(self, path: str, need: str = "x") -> bool:
        """
        need: "r" | "w" | "x" | combinations like "rw", "rwx"

        Rules, evaluated in order:
          1. An explicit grant on the path itself wins over all ancestor
             denies (an explicitly allowed area stays usable). Only denies
             on the path itself reduce it.
          2. Otherwise allows and denies accumulate along the chain;
             effective = union(allow) - union(deny); a deny removes only
             its own bits.
          3. Traversal: pure READ on a container reached via a deeper
             grant is guaranteed — the path to your rights is always
             reachable, ancestor denies cannot remove it.
        """
        need_bits = PermBits.from_str(need)

        # Ancestor allows always accumulate.
        allow_bits = PermBits()
        for ancestor in _ancestors(path):
            allow = self._allow.get(ancestor)
            if allow:
                allow_bits = allow_bits.union(allow.bits)

        # A deny on the path itself (or an ancestor when there is no
        # self-grant) subtracts. An explicit self-grant makes the area
        # usable regardless of ancestor denies — only the self-deny
        # reduces it.
        self_allow = self._allow.get(path)
        if self_allow is not None:
            deny_bits = PermBits()
            self_deny = self._deny.get(path)
            if self_deny:
                deny_bits = deny_bits.union(self_deny.bits)
        else:
            deny_bits = PermBits()
            for ancestor in _ancestors(path):
                deny = self._deny.get(ancestor)
                if deny:
                    deny_bits = deny_bits.union(deny.bits)

        if allow_bits:
            eff = allow_bits.subtract(deny_bits)
            if _satisfies(eff, need_bits):
                return True

        # Traversal: pure READ on a container reached via a deeper grant.
        # Derived traversal is a guaranteed property of an explicit grant —
        # an explicitly allowed area is always reachable. Ancestor denies
        # cannot remove the derived path.
        if (
            need_bits.r
            and not need_bits.w
            and not need_bits.x
            and self._has_descendant_grant(path)
        ):
            return True

        return False

    def _has_descendant_grant(self, path: str) -> bool:
        """True if an allow grant lies underneath *path* (segment-based)."""
        prefix = _child_prefix(path)
        return any(k.startswith(prefix) for k in self._allow)

    def clone(self) -> PermissionSet:

        out = PermissionSet()

        out._allow = self._allow.copy()
        out._deny = self._deny.copy()

        return out

    def to_debug_dict(self) -> dict[str, dict[str, str]]:

        def bits_to_str(b: PermBits | None) -> str:
            if not b:
                return ""
            return ("r" if b.r else "") + ("w" if b.w else "") + ("x" if b.x else "")

        out: dict[str, dict[str, str]] = {}
        keys = set(self._allow.keys()) | set(self._deny.keys())
        for k in sorted(keys):
            a = self._allow.get(k)
            d = self._deny.get(k)
            out[k] = {
                "allow": bits_to_str(a.bits) if a else "",
                "deny": bits_to_str(d.bits) if d else "",
            }
        return out


def _satisfies(eff: PermBits, need: PermBits) -> bool:
    if need.r and not eff.r:
        return False
    if need.w and not eff.w:
        return False
    if need.x and not eff.x:
        return False
    return True


def _ancestors(path: str) -> list[str]:
    """Return path and all its ancestors, most specific first.

    "/usr/bin/ls" -> ["/usr/bin/ls", "/usr/bin", "/usr", "/"]
    """
    normalized = path.strip()
    if not normalized:
        return ["/"]

    parts = [p for p in normalized.strip("/").split("/") if p]
    if not parts:
        return ["/"]

    out: list[str] = []
    for i in range(len(parts), 0, -1):
        out.append("/" + "/".join(parts[:i]))
    out.append("/")
    return out


def _child_prefix(path: str) -> str:
    """Segment prefix for descendants of *path*.

    "/usr" -> "/usr/"; "/" -> "/"
    """
    if path == "/":
        return "/"
    return path.rstrip("/") + "/"
