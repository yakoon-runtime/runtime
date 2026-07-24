from __future__ import annotations

from pathlib import Path

from yak.distribution.target import TargetResolver
from yak.hosts.cli.parser import build_parser
from yak.installation.manager import InstallationManager


def _build_manager() -> InstallationManager:
    repo_root = Path(__file__).resolve().parents[5]
    dists_root = repo_root / "yak" / "distributions"
    inst_root = repo_root / "workspace"
    target = TargetResolver(dists_root, repo_root / "repos", repo_root / "runtime")
    return InstallationManager(
        target, inst_root, repo_root / "repos", repo_root / "runtime"
    )


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    manager = _build_manager()
    args.func(args, manager)


if __name__ == "__main__":
    main()
