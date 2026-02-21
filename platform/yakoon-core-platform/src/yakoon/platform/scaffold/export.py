import shutil
from pathlib import Path
from zipfile import ZipFile

MESH_SOURCE = Path("yakoon/mesh")


def copy_mesh_runtime(target_dir: Path):
    """
    Copy yakoon/mesh into the given target directory (e.g. for export purposes).
    """
    if target_dir.exists():
        shutil.rmtree(target_dir)
    shutil.copytree(MESH_SOURCE, target_dir)
    print(f"✅ Mesh runtime copied to {target_dir}")


def ensure_real_runtime(path: Path):
    if path.is_symlink():
        print("🔁 Converting symlink to real runtime copy")
        target = path.resolve()
        path.unlink()
        shutil.copytree(target, path)


def zip_directory(source_dir: Path, zip_path: Path):
    """
    Zip an entire directory recursively into a .zip file.
    """
    with ZipFile(zip_path, "w") as zipf:
        for file in source_dir.rglob("*"):
            zipf.write(file, arcname=file.relative_to(source_dir))
    print(f"✅ Directory zipped to {zip_path}")
