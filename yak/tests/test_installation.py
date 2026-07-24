import tempfile
from pathlib import Path

from yak.distribution.target import TargetResolver
from yak.installation.manager import InstallationManager


def test_install_creates_installation():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repos = root / "repos"
        dists = root / "dists"
        installations = root / "inst"

        # Create a pack with structure
        (repos / "test-pack" / "structure").mkdir(parents=True)
        (repos / "test-pack" / "pack.toml").write_text(
            'name = "test-pack"\nversion = "0.1"\n'
        )

        # Create a distribution
        dists.mkdir()
        (dists / "myapp.toml").write_text(
            'name = "myapp"\nversion = "0.1"\n\n[[packs]]\nname = "test-pack"\n'
        )

        target = TargetResolver(repos, dists)
        mgr = InstallationManager(target, repos, installations)

        inst = mgr.install("myapp")

        assert inst.name == "myapp"
        assert inst.distribution == "myapp"
        assert inst.packs == ["test-pack"]
        assert inst.root == installations / "myapp"
        assert (inst.root / "workspace.toml").exists()
        assert (inst.root / ".yak" / "state.toml").exists()


def test_install_unknown_target_raises():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = TargetResolver(root / "repos", root / "dists")
        mgr = InstallationManager(target, root / "repos", root / "inst")

        import pytest

        with pytest.raises(ValueError, match="Unknown target"):
            mgr.install("nonexistent")


def test_status_returns_none_for_unknown():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = TargetResolver(root / "repos", root / "dists")
        mgr = InstallationManager(target, root / "repos", root / "inst")

        assert mgr.status("unknown") is None


def test_statuses_returns_empty_when_no_installations():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        target = TargetResolver(root / "repos", root / "dists")
        mgr = InstallationManager(target, root / "repos", root / "inst")

        assert mgr.statuses() == []


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


def test_update_rematerializes():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repos, dists = _make_env(root)
        mgr = InstallationManager(TargetResolver(repos, dists), repos, root / "inst")
        mgr.install("myapp")
        mgr.update("myapp")
        inst = mgr.status("myapp")
        assert inst is not None
        assert inst.status.value == "materialized"


def test_doctor_reports_missing_pack():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repos, dists = _make_env(root)
        mgr = InstallationManager(TargetResolver(repos, dists), repos, root / "inst")
        mgr.install("myapp")

        # Remove pack after installation
        import shutil

        shutil.rmtree(repos / "test-pack")

        issues = mgr.doctor("myapp")
        assert any("test-pack" in i for i in issues)


def test_doctor_reports_missing_installation():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repos, dists = _make_env(root)
        mgr = InstallationManager(TargetResolver(repos, dists), repos, root / "inst")
        issues = mgr.doctor("nonexistent")
        assert "not found" in issues[0]


def test_update_unknown_raises():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        repos, dists = _make_env(root)
        mgr = InstallationManager(TargetResolver(repos, dists), repos, root / "inst")
        import pytest

        with pytest.raises(ValueError, match="not found"):
            mgr.update("nonexistent")
