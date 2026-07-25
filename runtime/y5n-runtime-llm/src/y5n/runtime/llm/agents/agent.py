from __future__ import annotations

import json
from collections.abc import AsyncGenerator, Iterable

from y5n.runtime.api.flow.channel import Scope
from y5n.runtime.api.flow.dsl import Outcome, out_text, receive, start_task
from y5n.runtime.api.llm import LLMMessage, LLMRequest, OnCallLLM


class AgentDone(Exception):
    """Signal that the agent wants to stop with a result."""

    def __init__(self, result: str):
        self.result = result


class AgentError(Exception):
    """Signal that the agent cannot fulfill the request."""

    def __init__(self, reason: str):
        self.reason = reason


def _find_json(raw: str) -> dict | None:
    """Extract the first complete JSON object from arbitrary text."""
    depth = 0
    start = -1
    for i, ch in enumerate(raw):
        if ch == "{":
            if depth == 0:
                start = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start >= 0:
                try:
                    return json.loads(raw[start : i + 1])
                except json.JSONDecodeError:
                    start = -1
    return None


class Agent:
    """Reusable multi-step agent loop.

    Encapsulates the pattern:
      system prompt -> LLM call -> parse -> execute -> observe -> loop -> done

    Usage in a handler:

        agent = Agent(llm, SYSTEM_PROMPT)
        yield agent.run(
            request="wie viele PDFs?",
            context={"user": "sbergmann"},
            blacklist={"rm", "sudo"},
        )
        yield out_text(agent.result)
    """

    def __init__(
        self,
        llm: OnCallLLM,
        prompt: str,
        *,
        max_steps: int = 10,
        max_repeat: int = 1,  # same action + same output twice in a row → loop
    ):
        self._llm = llm
        self._prompt = prompt
        self._max_steps = max_steps
        self._max_repeat = max_repeat
        self._channel = f"_agent_{id(self)}"
        self._loop_warning_given = False
        self.result: str | None = None

    async def run(
        self,
        request: str,
        *,
        context: dict[str, str] | None = None,
        blacklist: Iterable[str] = frozenset(),
    ) -> AsyncGenerator[Outcome, None]:
        """Run the agent loop.

        Yields effects (start_task, receive, out_text) to the runtime.
        After completion, ``self.result`` contains the answer.
        """
        _blacklist = frozenset(blacklist)

        messages = [
            LLMMessage(
                role="system",
                content=self._prompt.format(**(context or {})),
            ),
            LLMMessage(role="user", content=request),
        ]

        step = 0
        last_fingerprint: int | None = None
        repeat_count = 0

        while True:

            # -----------------
            # THINK
            # -----------------

            response = await self._llm.complete(LLMRequest(messages=messages))
            parsed = _find_json(response.text)

            if parsed is None:
                self.result = f"invalid response: {response.text}"
                return

            if "done" in parsed:
                self.result = parsed.get("result", "")
                return

            if "error" in parsed:
                self.result = f"error: {parsed['error']}"
                return

            command = parsed.get("command", "")
            args = parsed.get("args", [])

            if not command or command in _blacklist:
                self.result = f"rejected: {command}" if command else "invalid response"
                return

            # -----------------
            # ACT
            # -----------------

            display = command if not args else f"{command} {' '.join(args)}"
            yield out_text(f"$ {display}")

            yield start_task(
                command, channel=self._channel, args=args, scope=Scope.FLOW
            )
            event = yield receive(self._channel, scope=Scope.FLOW)
            payload = event.payload

            if isinstance(payload, dict) and "error" in payload:
                self.result = f"failed: {payload['error']}"
                return

            stdout = payload.get("stdout", "")
            stderr = payload.get("stderr", "")
            returncode = payload.get("returncode", 0)

            # -----------------
            # LOOP DETECTION
            # -----------------

            fingerprint = hash((command, tuple(args), stdout, stderr, returncode))
            if fingerprint == last_fingerprint:
                repeat_count += 1
            else:
                last_fingerprint = fingerprint
                repeat_count = 0

            if repeat_count >= self._max_repeat:
                if self._loop_warning_given:
                    self.result = "loop detected: same command produces same result"
                    return
                self._loop_warning_given = True
                repeat_count = 0
                last_fingerprint = None
                yield out_text(
                    "! Wiederhole dieselbe Aktion — versuche anderen Ansatz."
                )
                messages.append(
                    LLMMessage(
                        role="user",
                        content="Du wiederholst dieselbe Aktion mit demselben Ergebnis. Versuche einen anderen Ansatz.",
                    )
                )
                step += 1
                if step >= self._max_steps:
                    self.result = "max steps exceeded"
                    return
                continue

            # -----------------
            # OBSERVE
            # -----------------

            output_lines = []
            if stdout:
                output_lines.append(stdout.rstrip())
            if stderr:
                output_lines.append(f"stderr: {stderr.rstrip()}")

            output = "\n".join(output_lines)
            if output:
                yield out_text(output)

            messages.append(LLMMessage(role="assistant", content=json.dumps(parsed)))
            messages.append(
                LLMMessage(
                    role="user",
                    content=(
                        f"Kommando beendet (returncode: {returncode}):\n"
                        f"{output}\n"
                        f"Fahre fort oder antworte mit done."
                    ),
                )
            )

            step += 1
            if step >= self._max_steps:
                self.result = "max steps exceeded"
                return
