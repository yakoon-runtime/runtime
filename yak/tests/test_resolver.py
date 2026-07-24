from yak.distribution.models import Distribution, PackName, PackReference
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
    result = resolver.resolve(dist)

    assert result == [PackName("runtime"),
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
    result = resolver.resolve(crm)

    assert result == [PackName("runtime"),
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
    result = resolver.resolve(combined)

    assert result == [PackName("shared"),
                      PackName("a-only"),
                      PackName("b-only")]
