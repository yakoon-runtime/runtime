import shutil
from pathlib import Path

from yakoon.platform.scaffold.export import ensure_real_runtime

TEMPLATE_DIR = Path(__file__).parent / "template"


def scaffold_workspace(app_name: str, target_dir: Path):
    """
    Copy the scaffold template and rewrite imports to match the new app namespace.
    """
    if target_dir.exists():
        raise FileExistsError(f"Target directory '{target_dir}' already exists.")

    shutil.copytree(TEMPLATE_DIR, target_dir)
    ensure_real_runtime(target_dir / "runtime")
    rewrite_imports(target_dir, app_name)
    print(f"✅ Scaffold '{app_name}' created at {target_dir}")


def rewrite_imports(path: Path, app_name: str):
    """
    Replace yakoon.* imports with app-local equivalents in all .py files under `path`.
    """
    replacements = [
        ("from yakoon.mesh", f"from {app_name}.runtime"),
        ("import yakoon.mesh", f"import {app_name}.runtime"),
        ("from yakoon", f"from {app_name}"),
        ("import yakoon", f"import {app_name}"),
    ]

    for file in path.rglob("*.py"):
        if not file.is_file():
            continue
        content = file.read_text(encoding="utf-8")
        new_content = content
        for old, new in replacements:
            new_content = new_content.replace(old, new)
        if new_content != content:
            file.write_text(new_content, encoding="utf-8")
