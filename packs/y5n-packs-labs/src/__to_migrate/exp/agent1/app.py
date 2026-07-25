from __future__ import annotations

import getpass
import os as stdlib_os
import platform

from y5n.runtime.api.dsl import out_text
from y5n.runtime.api.nodes import NodeSpace
from y5n.runtime.api.ports import OnCallLLM
from y5n.runtime.llm.agents import Agent
from y5n.runtime.llm.providers.openai_compat import OpenAICompatibleProvider

MAX_STEPS = 10

BLACKLIST = {
    "rm",
    "sudo",
    "su",
    "passwd",
    "shutdown",
    "reboot",
    "systemctl",
    "curl",
    "wget",
    "scp",
    "ssh",
    "mkfs",
    "dd",
    "fdisk",
    "chmod",
    "chown",
    "kill",
    "apt",
    "dnf",
    "yum",
    "pip",
    "npm",
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


async def run(space: NodeSpace):
    space.ports.provide(
        OnCallLLM,
        OpenAICompatibleProvider(
            base_url="https://api.mistral.ai/v1",
            model="mistral-large-latest",
            api_key=stdlib_os.environ.get("MISTRAL_API_KEY"),
        ),
    )

    request = " ".join(space.request.args())
    if not request:
        yield out_text("Usage: agent1 <frage>")
        return

    llm = space.ports.get(OnCallLLM)
    user = getpass.getuser()
    home = stdlib_os.path.expanduser("~")
    cwd = stdlib_os.getcwd()
    system = f"{platform.system()} {platform.release()}"

    agent = Agent(llm=llm, prompt=SYSTEM_PROMPT, max_steps=MAX_STEPS)

    yield agent.run(
        request=request,
        context={"user": user, "home": home, "cwd": cwd, "system": system},
        blacklist=BLACKLIST,
    )

    yield out_text(agent.result or "")
