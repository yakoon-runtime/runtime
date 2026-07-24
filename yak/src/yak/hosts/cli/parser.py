from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    from yak.hosts.cli.commands import doctor as _doctor
    from yak.hosts.cli.commands import install as _install
    from yak.hosts.cli.commands import resolve as _resolve
    from yak.hosts.cli.commands import shell as _shell
    from yak.hosts.cli.commands import start as _start
    from yak.hosts.cli.commands import status as _status
    from yak.hosts.cli.commands import stop as _stop
    from yak.hosts.cli.commands import update as _update
    from yak.hosts.cli.commands import web as _web

    parser = argparse.ArgumentParser(
        prog="yak",
        description="Yakoon Platform Manager",
        usage="yak <command> [options]",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "  Lifecycle\n"
            "    install    Install a distribution\n"
            "    update     Update an installation\n"
            "    status     Show installation status\n"
            "    doctor     Check installation health\n"
            "    start      Start runtime of an installation\n"
            "    stop       Stop runtime of an installation\n"
            "\n"
            "  Interfaces\n"
            "    shell      Open the Yakoon shell\n"
            "    web        Open the Yakoon web interface\n"
            "\n"
            "  Developer\n"
            "    resolve    Show resolved pack list for a target\n"
        ),
    )
    sub = parser.add_subparsers(dest="command", required=True, metavar="<command>")

    p = sub.add_parser("resolve", help="")
    p.add_argument("target")
    p.set_defaults(func=_resolve.run)

    p = sub.add_parser("install", help="")
    p.add_argument("target")
    p.add_argument("--path", "-p", help="Installation path (default: ./<target>)")
    p.add_argument("--verbose", "-v", action="store_true", help="Show detailed progress")
    p.set_defaults(func=_install.run)

    p = sub.add_parser("status", help="")
    p.add_argument("--path", "-p", help="Path to installation (default: current directory)")
    p.set_defaults(func=_status.run)

    p = sub.add_parser("update", help="")
    p.add_argument("--path", "-p", help="Path to installation")
    p.add_argument("--verbose", "-v", action="store_true", help="Show detailed progress")
    p.set_defaults(func=_update.run)

    p = sub.add_parser("doctor", help="")
    p.add_argument("--path", "-p", help="Path to installation")
    p.set_defaults(func=_doctor.run)

    p = sub.add_parser("start", help="")
    p.add_argument("--path", "-p", help="Path to installation")
    p.set_defaults(func=_start.run)

    p = sub.add_parser("stop", help="")
    p.add_argument("--path", "-p", help="Path to installation")
    p.set_defaults(func=_stop.run)

    p = sub.add_parser("shell", help="")
    p.add_argument("--path", "-p", help="Path to installation")
    p.set_defaults(func=_shell.run)

    p = sub.add_parser("web", help="")
    p.add_argument("--path", "-p", help="Path to installation")
    p.set_defaults(func=_web.run)

    return parser
