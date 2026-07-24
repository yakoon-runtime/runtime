from yak.distribution.models import Distribution, PackName, PackReference
from yak.resolver.resolver import Resolver


class FakeRepository:
    def __init__(self) -> None:
        self._distributions: dict[str, Distribution] = {}
        self._packs: set[PackName] = set()

    def add_distribution(self, dist: Distribution) -> None:
        self._distributions[dist.name] = dist
        for ref in dist.packs:
            self._packs.add(ref.name)

    def resolve_distribution(self, name: str) -> Distribution | None:
        return self._distributions.get(name)

    def resolve_pack(self, name: PackName) -> bool:
        return name in self._packs


def test_resolve_single_distribution():
    repo = FakeRepository()
    repo.add_distribution(Distribution(
        name="crm",
        version="1.0",
        packs=[PackReference(name=PackName("runtime")),
               PackReference(name=PackName("system")),
               PackReference(name=PackName("ident")),
               PackReference(name=PackName("crm"))],
    ))

    resolver = Resolver(repo)
    result = resolver.resolve("crm")

    assert result == [PackName("runtime"),
                      PackName("system"),
                      PackName("ident"),
                      PackName("crm")]


def test_resolve_nested_distributions():
    repo = FakeRepository()
    repo.add_distribution(Distribution(
        name="base",
        version="1.0",
        packs=[PackReference(name=PackName("runtime")),
               PackReference(name=PackName("system"))],
    ))
    repo.add_distribution(Distribution(
        name="crm",
        version="1.0",
        distributions=[PackReference(name=PackName("base"))],
        packs=[PackReference(name=PackName("ident")),
               PackReference(name=PackName("crm"))],
    ))

    resolver = Resolver(repo)
    result = resolver.resolve("crm")

    assert result == [PackName("runtime"),
                      PackName("system"),
                      PackName("ident"),
                      PackName("crm")]


def test_resolve_deduplicates():
    repo = FakeRepository()
    repo.add_distribution(Distribution(
        name="a",
        version="1.0",
        packs=[PackReference(name=PackName("shared")),
               PackReference(name=PackName("a-only"))],
    ))
    repo.add_distribution(Distribution(
        name="b",
        version="1.0",
        packs=[PackReference(name=PackName("shared")),
               PackReference(name=PackName("b-only"))],
    ))
    repo.add_distribution(Distribution(
        name="combined",
        version="1.0",
        distributions=[PackReference(name=PackName("a")),
                       PackReference(name=PackName("b"))],
    ))

    resolver = Resolver(repo)
    result = resolver.resolve("combined")

    assert result == [PackName("shared"),
                      PackName("a-only"),
                      PackName("b-only")]
