from __future__ import annotations

import asyncio

from yakoon.base.host import FormInput, TextInput

from .runner import Runner


class RuntimeHost:

    def __init__(self, engine, session, bus):
        self.engine = engine
        self.session = session
        self.bus = bus
        self.runner = None

    async def connect(self, connection, host_adapter):
        self.bus.join(connection)
        if self.runner is None:
            self.runner = Runner(
                engine=self.engine,
                session=self.session,
                interaction=host_adapter,
            )
            asyncio.create_task(self.runner.start([]))
        return connection

    async def receive_input(self, event):
        if self.runner is None:
            raise RuntimeError("Runner must not be Null.")
        if isinstance(event, FormInput):
            await self.runner.on_input_submit(event.data)
        elif isinstance(event, TextInput):
            await self.runner.on_user_input(event.value)
