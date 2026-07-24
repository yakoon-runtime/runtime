from __future__ import annotations

from pathlib import Path

from yak.hosts.cli.parser import build_parser
from yak.installation.manager import InstallationManager
from yak.repository.artifact import DirectoryArtifactStore
from yak.repository.file_repo import FileRepository


def _build_manager() -> InstallationManager:
    repo_root = Path(__file__).resolve().parents[5]
    repos = repo_root / "repos"
    runtime = repo_root / "runtime"
    dists = repo_root / "yak" / "distributions"
    inst_root = repo_root / "workspace"

    repo = FileRepository(repos, runtime, builtin_dists=dists)
    artifacts = DirectoryArtifactStore(repos, runtime)
    return InstallationManager(repo, artifacts, inst_root)


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    manager = _build_manager()
    args.func(args, manager)


if __name__ == "__main__":
    main()
