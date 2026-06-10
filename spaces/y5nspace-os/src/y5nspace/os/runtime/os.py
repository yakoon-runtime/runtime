from __future__ import annotations

import asyncio
import getpass
import json
import os as stdlib_os
import platform

from y5n.api.dsl import out_text, receive, start_task
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnCallLLM
from y5n.base.flow.channel import Scope
from y5n.base.llm import LLMMessage, LLMRequest

CHANNEL = "os-result"
MAX_STEPS = 10

BLACKLIST = {
    "rm", "sudo", "su", "passwd", "shutdown", "reboot",
    "systemctl", "curl", "wget", "scp", "ssh",
    "mkfs", "dd", "fdisk", "chmod", "chown", "kill",
    "apt", "dnf", "yum", "pip", "npm",
}

SYSTEM_PROMPT = """Du bist ein OS-Assistent.

Kontext der Sitzung:
  Benutzer:     {user}
  Home:         {home}
  Arbeitsverz:  {cwd}
  System:       {system}

Du kannst mehrere Kommandos nacheinander ausführen.
Nach jedem Kommando siehst du die Ausgabe und entscheidest,
ob du fertig bist oder ein weiteres Kommando brauchst.

Antworte in einem der folgenden JSON-Formate:

1. Kommando ausführen:
  {{"command": "ls", "args": ["-la", "/tmp"]}}

2. Fertig — Ergebnis ausgeben:
  {{"done": true, "result": "Deine Antwort"}}

3. Fehler — kann nicht beantwortet werden:
  {{"error": "Begründung"}}

Verfügbare Kommandos (nur lesend):
  ls, find, du, df, free, ps, uname, whoami, id, groups,
  uptime, date, pwd, which, cat, head, tail, wc, file, stat,
  lsblk, lscpu, lsusb, lspci, echo, lsof, mount, dmesg, journalctl

Regeln:
- Verwende nur existierende Optionen. Erfinde keine.
- Kein sudo, kein su, keine Änderungen.
- Keine GUI-Programme.
- Keine Pipes, Heredocs, Redirects, Wildcards.
- Keine Shell-Syntax — kein $(), keine Backticks, keine Variablen.
- Nur ein JSON-Objekt pro Antwort. Keine Erklärungen."""


def _find_json(raw: str) -> dict | None:
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


async def run(space: NodeSpace):
    request = " ".join(space.request.args())
    if not request:
        yield out_text("Usage: os <frage>")
        return

    llm: OnCallLLM = space.ports.get(OnCallLLM)
    user = getpass.getuser()
    home = stdlib_os.path.expanduser("~")
    cwd = stdlib_os.getcwd()
    system = f"{platform.system()} {platform.release()}"

    messages = [
        LLMMessage(
            role="system",
            content=SYSTEM_PROMPT.format(user=user, home=home, cwd=cwd, system=system),
        ),
        LLMMessage(role="user", content=request),
    ]

    for step in range(MAX_STEPS):
        result = await llm.complete(LLMRequest(messages=messages))
        try:
            parsed = _find_json(result.text)
            if parsed is None:
                raise json.JSONDecodeError("no json found", result.text, 0)
        except json.JSONDecodeError:
            yield out_text(f"invalid response: {result.text}")
            return

        if "done" in parsed:
            yield out_text(parsed.get("result", ""))
            return

        if "error" in parsed:
            yield out_text(f"error: {parsed['error']}")
            return

        command = parsed.get("command", "")
        args = parsed.get("args", [])

        if not command or command in BLACKLIST:
            yield out_text(f"rejected: {command}" if command else "invalid response")
            return

        display = command if not args else f"{command} {' '.join(args)}"
        yield out_text(f"$ {display}")

        yield start_task(command, channel=CHANNEL, args=args)
        event = yield receive(CHANNEL, scope=Scope.SESSION)
        payload = event.payload

        if isinstance(payload, dict) and "error" in payload:
            yield out_text(f"failed: {payload['error']}")
            return

        stdout = payload.get("stdout", "")
        stderr = payload.get("stderr", "")
        returncode = payload.get("returncode", 0)

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

    yield out_text("os: zu viele Schritte — abgebrochen")
