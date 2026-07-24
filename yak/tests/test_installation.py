import tempfile
from pathlib import Path

from yak.installation.manager import InstallationManager
from yak.repository.artifact import DirectoryArtifactStore
from yak.repository.file_repo import FileRepository


def _make_env(root, pack_name="test-pack"):
    repos = root / "repos"
    dists = root / "dists"
    (repos / pack_name / "structure").mkdir(parents=True)
    (repos / pack_name / "pack.toml").write_text(
        f'name = "{pack_name}"\nversion = "0.1"\n'
    )
    dists.mkdir()
    (dists / "myapp.toml").write_text(
        f'name = "myapp"\nversion = "0.1"\n\n[[packs]]\nname = "{pack_name}"\n'
    )
    return repos, dists


def _mgr(repos, dists, installations):
    repo = FileRepository(repos, builtin_dists=dists)
    artifacts = DirectoryArtifactStore(repos)
    return InstallationManager(repo, artifacts, installations)


def test_install_creates_installation():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repos, dists = _make_env(root)
        mgr = _mgr(repos, dists, root / "inst")

        inst = mgr.install("myapp")

        assert inst.name == "myapp"
        assert inst.distribution == "myapp"
        assert inst.packs == ["test-pack"]
        assert inst.root == root / "inst" / "myapp"
        assert (inst.root / "workspace.toml").exists()
        assert (inst.root / ".yak" / "state.toml").exists()


def test_install_unknown_target_raises():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = FileRepository(root / "repos", builtin_dists=root / "dists")
        artifacts = DirectoryArtifactStore(root / "repos")
        mgr = InstallationManager(repo, artifacts, root / "inst")

        import pytest

        with pytest.raises(ValueError, match="Unknown target"):
            mgr.install("nonexistent")


def test_status_returns_none_for_unknown():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = FileRepository(root / "repos", builtin_dists=root / "dists")
        artifacts = DirectoryArtifactStore(root / "repos")
        mgr = InstallationManager(repo, artifacts, root / "inst")

        assert mgr.status("unknown") is None


def test_statuses_returns_empty_when_no_installations():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repo = FileRepository(root / "repos", builtin_dists=root / "dists")
        artifacts = DirectoryArtifactStore(root / "repos")
        mgr = InstallationManager(repo, artifacts, root / "inst")

        assert mgr.statuses() == []


def test_update_rematerializes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repos, dists = _make_env(root)
        mgr = _mgr(repos, dists, root / "inst")
        mgr.install("myapp")
        mgr.update("myapp")
        inst = mgr.status("myapp")
        assert inst is not None
        assert inst.status.value == "materialized"


def test_doctor_reports_missing_pack():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repos, dists = _make_env(root)
        mgr = _mgr(repos, dists, root / "inst")
        mgr.install("myapp")

        import shutil

        shutil.rmtree(repos / "test-pack")

        issues = mgr.doctor("myapp")
        assert any("test-pack" in i for i in issues)


def test_doctor_reports_missing_installation():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repos, dists = _make_env(root)
        mgr = _mgr(repos, dists, root / "inst")
        issues = mgr.doctor("nonexistent")
        assert "not found" in issues[0]


def test_update_unknown_raises():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repos, dists = _make_env(root)
        mgr = _mgr(repos, dists, root / "inst")
        import pytest

        with pytest.raises(ValueError, match="not found"):
            mgr.update("nonexistent")
