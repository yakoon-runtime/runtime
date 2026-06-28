from __future__ import annotations

import pytest

try:
    from y5nstore.sequence.allocator import ShardAllocator
    from y5nstore.sequence.backends.memory import MemoryShardRepository
    from y5nstore.sequence.runtime import Sequencer
except ImportError:
    pytest.skip("y5nstore.sequence not installed", allow_module_level=True)


@pytest.fixture
def repository() -> MemoryShardRepository:
    return MemoryShardRepository()


@pytest.fixture
async def sequencer(repository: MemoryShardRepository) -> Sequencer:
    allocator = ShardAllocator(repository, range_size=100)
    return Sequencer(allocator)


class TestMemorySequencer:

    async def test_next_id_returns_string(self, sequencer: Sequencer) -> None:
        id_ = await sequencer.next_id("test")
        assert isinstance(id_, str)

    async def test_next_id_increments(self, sequencer: Sequencer) -> None:
        a = await sequencer.next_id("test")
        b = await sequencer.next_id("test")
        assert int(b) == int(a) + 1

    async def test_next_id_separate_prefixes(self, sequencer: Sequencer) -> None:
        a = await sequencer.next_id("foo")
        b = await sequencer.next_id("bar")
        assert a == "1"
        assert b == "1"

    async def test_shard_wraps_after_range(self, repository: MemoryShardRepository) -> None:
        allocator = ShardAllocator(repository, range_size=5)
        seq = Sequencer(allocator)

        ids = []
        for _ in range(10):
            ids.append(await seq.next_id("wrapping"))

        assert ids == ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"]

    async def test_multiple_shards_are_unique(self, sequencer: Sequencer) -> None:
        ids = set()
        for _ in range(200):
            ids.add(await sequencer.next_id("unique"))
        assert len(ids) == 200
