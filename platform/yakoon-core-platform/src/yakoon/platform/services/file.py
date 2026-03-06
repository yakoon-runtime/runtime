import importlib.resources as ir
from dataclasses import dataclass
from pathlib import PurePosixPath

from yakoon.base.models.resource import _clean_rel
from yakoon.base.runtime.controllers.resources import ResourceRef


@dataclass(slots=True)
class FileLoader:
    """
    Generic loader for any resource under a package.

    Lookup order:
      1) host overrides (filesystem)  [optional, if you add it later]
      2) plugin/module package resources
      3) platform defaults (optional)
    """

    platform_package: str = ""
    platform_root: str = ""  # e.g. "templates" or "resources"
    # if you still want prefix filtering, keep sources; otherwise just use ref.package
    allowed_packages: set[str] | None = None

    def load_text(
        self,
        ref: ResourceRef,
        *,
        exts: tuple[str, ...] = (".yaml", ".yml", ".json"),
        encoding: str = "utf-8",
    ) -> str:
        # Optional: enforce allowed packages (security / sanity)
        if (
            self.allowed_packages is not None
            and ref.package not in self.allowed_packages
        ):
            raise LookupError(f"Package not allowed: {ref.package}")

        if not ref.package:
            raise LookupError(f"ResourceRef package cannot be None or Empty: {ref}")

        # 1) plugin/module package
        text = self._try_package(ref.package, ref.path, exts=exts, encoding=encoding)
        if text is not None:
            return text

        # 2) platform defaults (optional)
        if self.platform_package and self.platform_root:
            platform_path = str(
                PurePosixPath(self.platform_root) / _clean_rel(ref.path)
            )
            text = self._try_package(
                self.platform_package, platform_path, exts=exts, encoding=encoding
            )
            if text is not None:
                return text

        raise LookupError(
            f"Resource missing: {ref.package}:{ref.path} ({', '.join(exts)})"
        )

    def _try_package(
        self,
        package: str,
        rel_path_no_ext: str,
        *,
        exts: tuple[str, ...],
        encoding: str,
    ) -> str | None:
        base = ir.files(package)
        rel = _clean_rel(rel_path_no_ext)

        for ext in exts:
            candidate = base.joinpath(rel + ext)
            try:
                if candidate.is_file():
                    return candidate.read_text(encoding=encoding)
            except FileNotFoundError:
                # importlib.resources can throw for missing paths depending on backend
                pass

        return None
