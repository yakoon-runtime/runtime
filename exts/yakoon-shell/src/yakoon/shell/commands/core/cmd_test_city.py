from yakoon.base.commands import Command, Request
from yakoon.base.flow import present


class CmdTestCity(Command):

    key = "city.show.all"

    async def run(self, request: Request):

        offset = int(request.option("offset", 0))
        limit = 10

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

        projector = await self.create_projector()

        projection = await projector.project("show", state=state)
        yield present(projection)

    def get_data(self, offset: int, limit: int) -> tuple[list[str], int]:

        data = [f"{i:03}" for i in range(1, 100)]  # 001–099

        total = len(data)

        items = data[offset : offset + limit]

        return items, total
