from dataclasses import dataclass


@dataclass
class Shard:
    prefix: str
    shard_id: int
    range_start: int
    range_end: int
    value: int
    created_at: str | None = None

    def is_full(self) -> bool:
        return self.value >= (self.range_end - self.range_start)

    def to_row(self) -> dict:
        return {
            "prefix": self.prefix,
            "shard_id": self.shard_id,
            "range_start": self.range_start,
            "range_end": self.range_end,
            "value": self.value,
            "created_at": self.created_at,
        }

    @classmethod
    def from_row(cls, row: dict) -> "Shard":
        return cls(
            prefix=row["prefix"],
            shard_id=row["shard_id"],
            range_start=row["range_start"],
            range_end=row["range_end"],
            value=row["value"],
            created_at=row.get("created_at"),
        )
