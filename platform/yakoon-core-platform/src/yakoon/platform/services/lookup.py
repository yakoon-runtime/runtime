from requests import Request, Session


class NoLookupResolverService:

    async def resolve(self, session: Session, request: Request) -> str | None:
        return None
