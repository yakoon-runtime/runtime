from yak.distribution.models import Distribution, Mount, PackName, PackReference
from yak.resolver.resolver import Resolver


def lookup(distributions: dict[str, Distribution]):

    def resolve(name: str) -> Distribution | None:
        return distributions.get(name)

    return resolve


def test_resolve_single_distribution():
    dist = Distribution(
        name="crm",
        version="1.0",
        packs=[PackReference(name=PackName("runtime")),
               PackReference(name=PackName("system")),
               PackReference(name=PackName("ident")),
               PackReference(name=PackName("crm"))],
    )
    resolver = Resolver(lookup({"crm": dist}))
    packs, mounts = resolver.resolve(dist)

    assert packs == [PackName("runtime"),
                     PackName("system"),
                     PackName("ident"),
                     PackName("crm")]


def test_resolve_nested_distributions():
    base = Distribution(
        name="base",
        version="1.0",
        packs=[PackReference(name=PackName("runtime")),
               PackReference(name=PackName("system"))],
    )
    crm = Distribution(
        name="crm",
        version="1.0",
        distributions=[PackReference(name=PackName("base"))],
        packs=[PackReference(name=PackName("ident")),
               PackReference(name=PackName("crm"))],
    )
    resolver = Resolver(lookup({"base": base, "crm": crm}))
    packs, mounts = resolver.resolve(crm)

    assert packs == [PackName("runtime"),
                     PackName("system"),
                     PackName("ident"),
                     PackName("crm")]


def test_resolve_deduplicates():
    a = Distribution(
        name="a",
        version="1.0",
        packs=[PackReference(name=PackName("shared")),
               PackReference(name=PackName("a-only"))],
    )
    b = Distribution(
        name="b",
        version="1.0",
        packs=[PackReference(name=PackName("shared")),
               PackReference(name=PackName("b-only"))],
    )
    combined = Distribution(
        name="combined",
        version="1.0",
        distributions=[PackReference(name=PackName("a")),
                       PackReference(name=PackName("b"))],
    )
    resolver = Resolver(lookup({"a": a, "b": b, "combined": combined}))
    packs, mounts = resolver.resolve(combined)

    assert packs == [PackName("shared"),
                     PackName("a-only"),
                     PackName("b-only")]


def test_resolve_collects_mounts():
    base = Distribution(
        name="base",
        version="1.0",
        packs=[PackReference(name=PackName("system"))],
        mounts=[Mount(pack=PackName("system"), target="/usr/bin")],
    )
    crm = Distribution(
        name="crm",
        version="1.0",
        distributions=[PackReference(name=PackName("base"))],
        packs=[PackReference(name=PackName("crm"))],
        mounts=[Mount(pack=PackName("crm"), target="/opt/crm")],
    )
    resolver = Resolver(lookup({"base": base, "crm": crm}))
    packs, mounts = resolver.resolve(crm)

    assert packs == [PackName("system"), PackName("crm")]
    # Mounts from both base and crm are collected
    assert len(mounts) == 2
    assert Mount(pack=PackName("system"), target="/usr/bin") in mounts
    assert Mount(pack=PackName("crm"), target="/opt/crm") in mounts
