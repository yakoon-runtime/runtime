from __future__ import annotations

import argparse

from yak.hosts.cli.commands import (
    doctor,
    resolve,
    start,
    stop,
    update,
)
from yak.hosts.cli.commands import (
    install as install_cmd,
)
from yak.hosts.cli.commands import (
    status as status_cmd,
)

COMMANDS = {
    "resolve": resolve,
    "install": install_cmd,
    "status": status_cmd,
    "update": update,
    "doctor": doctor,
    "start": start,
    "stop": stop,
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="yak", description="Yakoon Platform Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("resolve", help="Show resolved pack list for a target")
    p.add_argument("target")
    p.set_defaults(func=resolve.run)

    p = sub.add_parser("install", help="Install a distribution")
    p.add_argument("target")
    p.set_defaults(func=install_cmd.run)

    p = sub.add_parser("status", help="Show installation status")
    p.add_argument("name", nargs="?")
    p.set_defaults(func=status_cmd.run)

    p = sub.add_parser("update", help="Update an installation")
    p.add_argument("name")
    p.set_defaults(func=update.run)

    p = sub.add_parser("doctor", help="Check installation health")
    p.add_argument("name")
    p.set_defaults(func=doctor.run)

    p = sub.add_parser("start", help="Start runtime of an installation")
    p.add_argument("name")
    p.set_defaults(func=start.run)

    p = sub.add_parser("stop", help="Stop runtime of an installation")
    p.add_argument("name")
    p.set_defaults(func=stop.run)

    return parser
