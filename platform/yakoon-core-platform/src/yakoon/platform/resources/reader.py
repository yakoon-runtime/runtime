import importlib.resources as ir
from dataclasses import dataclass
from pathlib import PurePosixPath

from yakoon.base.resources import ResourceRef


@dataclass(slots=True)
class PackageReader:

    def get_text(
        self,
        *,
        resource: ResourceRef,
        encoding: str = "utf-8",
    ) -> str:
        if not resource.package:
            raise LookupError("Parameter resource.package cannot be None or Empty")
        if not resource.path:
            raise LookupError("Parameter resource.path cannot be None or Empty")

        text = self._try_package(resource.package, resource.path, encoding=encoding)
        if text is not None:
            return text

        raise LookupError(f"Resource missing: {resource.package}:{resource.path}")

    def _try_package(
        self,
        package: str,
        name: str,
        *,
        encoding: str,
    ) -> str | None:
        base = ir.files(package)

        for ext in [".sam"]:
            if not name.endswith(ext):
                name += ext

            full_name = clean_rel(name)
            candidate = base.joinpath(full_name)
            try:
                if candidate.is_file():
                    return candidate.read_text(encoding=encoding)
            except FileNotFoundError:
                # importlib.resources can throw for missing paths depending on backend
                pass

        return None


def clean_rel(p: str) -> str:
    pp = PurePosixPath(p)
    if pp.is_absolute():
        pp = PurePosixPath(*pp.parts[1:])
    return str(pp)
