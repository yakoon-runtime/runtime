from yakoon.base.commands import Command, Request
from yakoon.base.commands.ports import OnProjectCmd
from yakoon.base.flow import out


class CmdTestCity(Command):

    key = "city.show.all"

    def __init__(self, on_project: OnProjectCmd):
        self.on_project = on_project

    async def run(self, request: Request):

        offset = int(request.option("offset", 0))
        limit = 5

        items, total = self.get_data(offset, limit)

        # Grenzen sauber halten
        max_offset = max(0, total - limit)
        offset = max(0, min(offset, max_offset))

        state = {
            "offset": offset,
            "limit": limit,
            "prev_offset": max(0, offset - limit),
            "next_offset": offset + limit,
            "has_prev": offset > 0,
            "has_next": offset + limit < total,
            "total": total,
            "items": items,
        }

        projection = await self.on_project(name="list.sam", state=state)
        yield out(projection)

    def get_data(self, offset: int, limit: int) -> tuple[list[str], int]:

        data = [f"{i:03}" for i in range(1, 100)]  # 001–099

        total = len(data)

        items = data[offset : offset + limit]

        return items, total
