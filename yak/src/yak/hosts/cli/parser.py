from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    from yak.hosts.cli.commands import doctor as _doctor
    from yak.hosts.cli.commands import install as _install
    from yak.hosts.cli.commands import resolve as _resolve
    from yak.hosts.cli.commands import start as _start
    from yak.hosts.cli.commands import status as _status
    from yak.hosts.cli.commands import stop as _stop
    from yak.hosts.cli.commands import update as _update

    parser = argparse.ArgumentParser(prog="yak", description="Yakoon Platform Manager")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("resolve", help="Show resolved pack list for a target")
    p.add_argument("target")
    p.set_defaults(func=_resolve.run)

    p = sub.add_parser("install", help="Install a distribution")
    p.add_argument("target")
    p.set_defaults(func=_install.run)

    p = sub.add_parser("status", help="Show installation status")
    p.add_argument("name", nargs="?")
    p.set_defaults(func=_status.run)

    p = sub.add_parser("update", help="Update an installation")
    p.add_argument("name")
    p.set_defaults(func=_update.run)

    p = sub.add_parser("doctor", help="Check installation health")
    p.add_argument("name")
    p.set_defaults(func=_doctor.run)

    p = sub.add_parser("start", help="Start runtime of an installation")
    p.add_argument("name")
    p.set_defaults(func=_start.run)

    p = sub.add_parser("stop", help="Stop runtime of an installation")
    p.add_argument("name")
    p.set_defaults(func=_stop.run)

    return parser
