from __future__ import annotations

import json
import os
import platform

from y5n.api.dsl import out_text, receive, start_task
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnCallLLM
from y5n.base.flow.channel import Scope
from y5n.base.llm import LLMMessage, LLMRequest
from y5n.llm.providers.openai_compat import OpenAICompatibleProvider

CHANNEL = "os-result"

BLACKLIST = {
    "rm", "sudo", "su", "passwd", "shutdown", "reboot",
    "systemctl", "curl", "wget", "scp", "ssh",
    "mkfs", "dd", "fdisk", "chmod", "chown", "kill",
    "apt", "dnf", "yum", "pip", "npm",
}

SYSTEM_PROMPT = """Du bist ein OS-Assistent für {system}.

Kommandos (nur lesend, nur existierende Optionen):

  ls       — Dateien auflisten
  find     — Dateien suchen
  du       — Dateigrößen
  df       — Festplattenbelegung
  free     — RAM/Swap
  ps       — Prozesse
  uname    — Systeminfo
  whoami   — Benutzer
  id       — Benutzer-IDs
  groups   — Gruppen
  uptime   — Laufzeit
  date     — Datum/Uhrzeit
  pwd      — Verzeichnis
  which    — Programm-Pfad
  cat      — Datei anzeigen
  head     — erste Zeilen
  tail     — letzte Zeilen
  wc       — Zähler
  file     — Dateityp
  stat     — Datei-Details
  lsblk    — Block-Geräte
  lscpu    — CPU
  lsusb    — USB
  lspci    — PCI
  echo     — Text ausgeben
  lsof     — offene Dateien/Prozesse
  mount    — Dateisysteme
  dmesg    — Kernel-Log
  journalctl — Systemd-Logs (--no-pager)

Antworte ausschließlich mit JSON:

{{"command": "ls", "args": ["-la", "/tmp"]}}

Regeln:
- command: eines der Kommandos oben.
- args: Liste der Argumente (kann leer sein []).
- Verwende nur existierende Optionen. Erfinde keine.
- Wenn eine Anfrage nicht passt: {{"error": "Begründung"}}.
- Kein sudo, kein su, keine Änderungen.
- Keine GUI-Programme (thunderbird, firefox, vi, nano).
- Keine Pipes, Heredocs, Redirects, Wildcards.
- Keine Shell-Syntax — nur Executable + Argumente.

Beispiele:
  "zeige Prozesse"       -> {{"command": "ps", "args": ["aux"]}}
  "wer bin ich"          -> {{"command": "whoami", "args": []}}
  "Speicher frei"        -> {{"command": "free", "args": ["-h"]}}
  "USB-Geräte"           -> {{"command": "lsusb", "args": []}}
  "Logs in /var/log"     -> {{"command": "ls", "args": ["-la", "/var/log"]}}
  "starte Firefox"       -> {{"error": "GUI-Programme sind nicht erlaubt"}}"""


async def run(space: NodeSpace):
    space.ports.provide(
        OnCallLLM,
        OpenAICompatibleProvider(
            base_url="https://api.mistral.ai/v1",
            model="mistral-large-latest",
            api_key=os.environ.get("MISTRAL_API_KEY"),
        ),
    )

    request = " ".join(space.request.args())
    if not request:
        yield out_text("Usage: agent2 <frage>")
        return

    llm = space.ports.get(OnCallLLM)
    system = f"{platform.system()} {platform.release()}"

    messages = [
        LLMMessage(role="system", content=SYSTEM_PROMPT.format(system=system)),
        LLMMessage(role="user", content=request),
    ]
    result = await llm.complete(LLMRequest(messages=messages))
    raw = result.text.strip()
    raw = raw.removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        yield out_text(f"invalid response: {raw}")
        return

    if "error" in parsed:
        yield out_text(f"error: {parsed['error']}")
        return

    command = parsed.get("command", "")
    args = parsed.get("args", [])

    if not command:
        yield out_text(f"invalid response: {raw}")
        return

    if command in BLACKLIST:
        yield out_text(f"rejected: {command}")
        return

    yield start_task(command, channel=CHANNEL, args=args)
    event = yield receive(CHANNEL, scope=Scope.SESSION)
    payload = event.payload

    if isinstance(payload, dict) and "error" in payload:
        yield out_text(f"failed: {payload['error']}")
        return

    stdout = payload.get("stdout", "")
    stderr = payload.get("stderr", "")

    if stdout:
        yield out_text(stdout)
    if stderr:
        yield out_text(f"stderr: {stderr}")
