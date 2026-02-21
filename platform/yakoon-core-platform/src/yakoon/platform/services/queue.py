from collections import deque

from yakoon.base.models.input import CommandDispatch, DispatchInput


class CommandQueueService:
    """
    Session-scoped command queue used to schedule follow-up commands.

    This service stores pending commands per session and is intentionally
    separated from the engine and commands themselves.

    Design goals:
    - Provide a single, explicit scheduling mechanism outside of commands.
    - Allow commands to enqueue follow-up steps dynamically (continue, retry, exit ...).
    - Keep the engine deterministic and non-interactive.
    - Ensure the host remains the only scheduler.

    Typical usage:
    - Batch commands enqueue multiple commands at once.
    - Interactive commands (e.g. login, wizards) enqueue next steps conditionally.
    - The host consumes commands from this queue between prompt handling and user input.
    """

    def __init__(self):
        """
        Initializes an empty command queue.

        Internally, commands are stored per session key to ensure strict
        isolation between concurrent sessions.
        """
        self._q: dict[str, deque[DispatchInput]] = {}

    def enqueue_commands(
        self, session, cmds: list[str], batch_id: str | None = None
    ) -> None:
        """
        Enqueues multiple commands at the front of the queue for the given session.

        Commands are inserted in a way that preserves their original execution order.

        This method is typically used by batch-like commands or workflow steps
        that want to schedule a sequence of follow-up commands.

        Args:
            session: The session for which the commands are scheduled.
            cmds: A list of command strings to enqueue.
        """
        skey = str(session.key)
        q = self._q.setdefault(skey, deque())

        for c in reversed(cmds):
            q.appendleft(CommandDispatch(text=c, batch_id=batch_id))

    def next_input(self, session) -> DispatchInput | None:
        """
        Retrieves and removes the next scheduled command for the given session.

        If the queue becomes empty after popping, it is automatically cleaned up
        to avoid leaking session state.

        Args:
            session: The session requesting the next command.

        Returns:
            The next command string if available, otherwise None.
        """
        skey = str(session.key)
        q = self._q.get(skey)
        if not q:
            return None

        item = q.popleft()
        if not q:
            self._q.pop(skey, None)

        return item

    def cancel_batch(self, session, batch_id: str) -> None:
        skey = str(session.key)
        q = self._q.get(skey)
        if not q:
            return

        self._q[skey] = deque(item for item in q if item.batch_id != batch_id)

        if not self._q[skey]:
            self._q.pop(skey, None)

    def has_pending(self, session) -> bool:
        """
        Checks whether there are pending commands for the given session.

        This is typically used by the host to decide whether the next input
        should come from the command queue or from the user.

        Args:
            session: The session to check.

        Returns:
            True if at least one command is queued for the session, otherwise False.
        """
        q = self._q.get(str(session.key))
        return bool(q)
