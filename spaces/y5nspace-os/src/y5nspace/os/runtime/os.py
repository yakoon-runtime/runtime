from __future__ import annotations

import platform
import shlex

from y5n.api.dsl import out_text, receive, start_task
from y5n.api.nodes import NodeSpace
from y5n.api.ports import OnCallLLM
from y5n.base.flow.channel import Scope
from y5n.base.llm import LLMMessage, LLMRequest

CHANNEL = "os-result"

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


def _is_safe(command: str) -> tuple[bool, str]:
    cmd = shlex.split(command)[0] if command else ""
    if cmd in BLACKLIST:
        return False, f"blocked: {cmd}"
    return True, ""


SYSTEM_PROMPT = """Du bist ein OS-Assistent für {system}.

Übersetze die Anfrage in EINES der folgenden Kommandos:

  ls       — Dateien auflisten
  find     — Dateien/Verzeichnisse suchen
  du       — Dateigrößen ermitteln
  df       — Festplattenbelegung
  free     — RAM-/Swap-Nutzung
  ps       — Prozesse anzeigen
  uname    — System-Info
  whoami   — aktueller Benutzer
  id       — Benutzer- und Gruppen-IDs
  groups   — Gruppen des Benutzers
  uptime   — System-Laufzeit
  date     — aktuelles Datum/Uhrzeit
  cal      — Kalender anzeigen
  pwd      — aktuelles Verzeichnis
  which    — Pfad eines Programms finden
  type     — Informationen zu einem Kommando
  env      — Umgebungsvariablen anzeigen
  locale   — Locale-Einstellungen
  cat      — Dateiinhalt ausgeben
  head     — erste Zeilen einer Datei
  tail     — letzte Zeilen einer Datei
  wc       — Zeilen-/Wort-/Zeichenzähler
  file     — Dateityp ermitteln
  stat     — detaillierte Datei-Info
  readlink — Ziel eines Symlinks anzeigen
  lsblk    — Block-Geräte anzeigen
  lscpu    — CPU-Informationen
  lsusb    — USB-Geräte anzeigen
  lspci    — PCI-Geräte anzeigen
  lshw     — Hardware-Informationen
  echo     — Text ausgeben
  printf   — formatierte Ausgabe
  lsof     — offene Dateien/Prozesse
  mount    — eingehängte Dateisysteme
  dmesg    — Kernel-Ringpuffer
  journalctl — Systemd-Logs (--no-pager)

Antworte NUR mit dem Kommando, ohne Erklärung, ohne Formatierung.
Beispiele:
  "zeige alle Prozesse"     → ps aux
  "wer bin ich"             → whoami
  "Speicher frei"           → free -h
  "Plattenbelegung"         → df -h
  "größte Dateien in /tmp"  → du -sh /tmp
  "welche Logs in /var/log" → ls -la /var/log
  "welche USB-Geräte"       → lsusb
  "wie lange läuft das Sys" → uptime
  "offene Netzwerk-Ports"   → lsof -i

Regeln:
- Kein sudo, kein su
- Nichts verändern — nur lesend
- Keine Pipe (|), keine Redirection (>, >>), kein Semikolon (;)
- Keine Shell-Wildcards (*) — das Kommando wird direkt ausgeführt"""


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
    result = await llm.complete(LLMRequest(messages=messages))
    raw = result.text.strip()

    safe, reason = _is_safe(raw)
    if not safe:
        yield out_text(f"rejected: {reason}")
        return

    parts = shlex.split(raw)
    command = parts[0]
    args = parts[1:]

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
