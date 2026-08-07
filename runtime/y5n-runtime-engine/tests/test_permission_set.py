"""PermissionSet inheritance semantics.

A grant on a path applies to that path and all its descendants
(segment-based inheritance). The most specific matching grant decides;
on the same level, deny wins over allow.
"""

from __future__ import annotations

from y5n.runtime.engine.capabilities.permission import PermissionParser, PermissionSet


def _add(permset: PermissionSet, spec: str) -> None:
    permset.add(PermissionParser().parse(spec))


def test_grant_applies_to_descendants():
    ps = PermissionSet()
    _add(ps, "/usr/bin|rwx")

    assert ps.check("/usr/bin", "x")
    assert ps.check("/usr/bin/ls", "x")
    assert ps.check("/usr/bin/cd", "x")
    assert ps.check("/usr/bin/help", "r")


def test_grant_does_not_leak_across_segments():
    ps = PermissionSet()
    _add(ps, "/usr/bin|rwx")

    assert not ps.check("/usr/binx", "x")
    assert not ps.check("/usr/sbin", "x")
    assert not ps.check("/opt", "x")
    assert not ps.check("/usr/binaries/ls", "x")


def test_exact_path_grants_work():
    ps = PermissionSet()
    _add(ps, "/crm/contact/edit|rx")

    assert ps.check("/crm/contact/edit", "r")
    assert ps.check("/crm/contact/edit", "x")
    assert not ps.check("/crm/contact/edit", "w")
    assert not ps.check("/crm/contact", "r")
    assert ps.check("/crm/contact/edit/extra", "r")


def test_deny_subtracts_on_same_level():
    ps = PermissionSet()
    _add(ps, "/usr/bin|rwx")
    _add(ps, "-/usr/bin|w")

    assert ps.check("/usr/bin/ls", "x")
    assert not ps.check("/usr/bin/ls", "w")
    assert ps.check("/usr/bin/ls", "r")


def test_deny_on_descendant_removes_only_its_bits():
    ps = PermissionSet()
    _add(ps, "/usr/bin|rwx")
    _add(ps, "-/usr/bin/shutdown|x")

    assert ps.check("/usr/bin/ls", "x")
    assert not ps.check("/usr/bin/shutdown", "x")
    assert ps.check("/usr/bin/shutdown", "r")
    assert ps.check("/usr/bin/shutdown", "w")


def test_root_grant_covers_everything():
    ps = PermissionSet()
    _add(ps, "/|r")

    assert ps.check("/", "r")
    assert ps.check("/usr/bin/ls", "r")
    assert not ps.check("/usr/bin/ls", "x")


def test_no_grant_denies():
    ps = PermissionSet()

    assert not ps.check("/usr/bin/ls", "x")
    assert not ps.check("/", "r")


def test_allows_accumulate_across_levels():
    ps = PermissionSet()
    _add(ps, "/crm|r")
    _add(ps, "/crm/contact|w")

    assert ps.check("/crm/contact", "r")
    assert ps.check("/crm/contact", "w")
    assert not ps.check("/crm/contact", "x")


def test_deny_can_shadow_an_allow_bit_from_ancestor():
    ps = PermissionSet()
    _add(ps, "/crm|rw")
    _add(ps, "-/crm/contact|w")

    assert ps.check("/crm/contact", "r")
    assert not ps.check("/crm/contact", "w")
    assert ps.check("/crm/notes", "w")
