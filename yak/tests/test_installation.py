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
