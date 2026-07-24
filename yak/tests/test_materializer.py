import tempfile
from pathlib import Path

from yak.distribution.models import PackName
from yak.repository.artifact import DirectoryArtifactStore
from yak.workspace.materializer import Materializer


def test_materialize_creates_workspace():
    with tempfile.TemporaryDirectory() as tmp:
        packs_root = Path(tmp) / "packs"
        ws_root = Path(tmp) / "workspace"

        pack_dir = packs_root / "test-pack" / "structure"
        pack_dir.mkdir(parents=True)
        (pack_dir / "hello.txt").write_text("hi")

        store = DirectoryArtifactStore(packs_root)
        mat = Materializer(store)
        ws = mat.materialize(ws_root, "test", [PackName("test-pack")])

        assert ws.path == ws_root
        assert ws.distribution == "test"
        assert ws.packs == [PackName("test-pack")]
        assert ws.created is not None
        assert ws.updated is not None

        manifest = ws_root / "workspace.toml"
        assert manifest.exists()
        assert "test-pack" in manifest.read_text()

        link = ws_root / "structure" / "test-pack"
        assert link.is_symlink()
        assert (link / "hello.txt").exists()
