class CommandManService:

    def __init__(self, source: CommandSource, on_has_permission):
        self.source = source
        self.on_has_permission = on_has_permission

    async def get_entries(self, app_id, session, mode, kind=None):

        result = await self.source.read(
            DataRequest(f"system:commands --by-app {app_id}")
        )

        rows = result.rows

        # Permission
        rows = [
            r
            for r in rows
            if self.on_has_permission(session=session, perm_key=f"{app_id}:{r['key']}")
        ]

        # Visibility
        allowed = self._allowed_visibilities(mode)
        rows = [r for r in rows if r["visibility"] in allowed]

        # Kind filter
        if kind:
            rows = [r for r in rows if r["kind"] == kind.name]

        return rows
