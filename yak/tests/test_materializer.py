import tempfile
from pathlib import Path

from yak.distribution.models import PackName
from yak.workspace.materializer import Materializer


def test_materialize_creates_workspace():
    with tempfile.TemporaryDirectory() as tmp:
        packs_root = Path(tmp) / "packs"
        ws_root = Path(tmp) / "workspace"

        # Create a fake pack with structure
        pack_dir = packs_root / "test-pack" / "structure"
        pack_dir.mkdir(parents=True)
        (pack_dir / "hello.txt").write_text("hi")

        mat = Materializer(packs_root)
        ws = mat.materialize(ws_root, "test", [PackName("test-pack")])

        assert ws.path == ws_root
        assert ws.distribution == "test"
        assert ws.packs == [PackName("test-pack")]
        assert ws.created is not None
        assert ws.updated is not None

        # workspace.toml exists
        manifest = ws_root / "workspace.toml"
        assert manifest.exists()
        assert "test-pack" in manifest.read_text()

        # structure symlink created
        link = ws_root / "structure" / "test-pack"
        assert link.is_symlink()
        assert (link / "hello.txt").exists()
