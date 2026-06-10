from __future__ import annotations

import asyncio
import json
import platform

from y5n.api.dsl import out_text, receive, start_task
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnCallLLM
from y5n.base.flow.channel import Scope
from y5n.base.llm import LLMMessage, LLMRequest

CHANNEL = "os-result"
MAX_RETRIES = 3

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
- Keine Shell-Syntax — kein $(), keine Backticks, keine Variablen.
- Nur ein JSON-Objekt pro Antwort. Keine Erklärungen.

Beispiele:
  "zeige Prozesse"       → {{"command": "ps", "args": ["aux"]}}
  "wer bin ich"          → {{"command": "whoami", "args": []}}
  "Speicher frei"        → {{"command": "free", "args": ["-h"]}}
  "USB-Geräte"           → {{"command": "lsusb", "args": []}}
  "Logs in /var/log"     → {{"command": "ls", "args": ["-la", "/var/log"]}}
  "starte Firefox"       → {{"error": "GUI-Programme sind nicht erlaubt"}}"""


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
    system = f"{platform.system()} {platform.release()}"

    messages = [
        LLMMessage(role="system", content=SYSTEM_PROMPT.format(system=system)),
        LLMMessage(role="user", content=request),
    ]

    for attempt in range(1 + MAX_RETRIES):
        result = await llm.complete(LLMRequest(messages=messages))
        try:
            parsed = _find_json(result.text)
            if parsed is None:
                raise json.JSONDecodeError("no json found", result.text, 0)
        except json.JSONDecodeError:
            yield out_text(f"invalid response: {result.text}")
            return

        if "error" in parsed:
            yield out_text(f"error: {parsed['error']}")
            return

        command = parsed.get("command", "")
        args = parsed.get("args", [])

        if not command or command in BLACKLIST:
            yield out_text(f"rejected: {command}" if command else "invalid response")
            return

        yield start_task(command, channel=CHANNEL, args=args)
        event = yield receive(CHANNEL, scope=Scope.SESSION)
        payload = event.payload

        if isinstance(payload, dict) and "error" in payload:
            yield out_text(f"failed: {payload['error']}")
            return

        stdout = payload.get("stdout", "")
        stderr = payload.get("stderr", "")
        returncode = payload.get("returncode", 0)

        if returncode == 0 and not stderr:
            if stdout:
                yield out_text(stdout)
            return

        if attempt < MAX_RETRIES:
            yield out_text(f"[retry {attempt + 1}/{MAX_RETRIES}]", mode="append")
            await asyncio.sleep(1)
            messages.append(
                LLMMessage(role="assistant", content=json.dumps(parsed))
            )
            messages.append(
                LLMMessage(
                    role="user",
                    content=(
                        f"Das Kommando ist fehlgeschlagen:\n"
                        f"returncode: {returncode}\n"
                        f"stderr: {stderr}\n"
                        f"stdout: {stdout}\n"
                        f"Versuche es mit einem korrigierten Kommando."
                    ),
                )
            )
        else:
            if stdout:
                yield out_text(stdout)
            if stderr:
                yield out_text(f"stderr: {stderr}")
            return
