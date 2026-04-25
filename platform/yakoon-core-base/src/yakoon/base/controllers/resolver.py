from pathlib import PurePosixPath


def resolve_resource(
    *,
    i18n_root: str | None,
    lang: str | None = None,
    cmd_key: str | None = None,
) -> str:
    """
    Resolve a resource location inside a package.
    Raises ValueError if root is None.
    """
    if not i18n_root:
        raise ValueError("Parameter i18n_root is None or Empty")

    cmd_key = clean_rel(cmd_key) if cmd_key else cmd_key
    root = i18n_root.format(lang=lang, cmd_key=cmd_key)
    root_rel = clean_rel(root)

    return root_rel


def clean_rel(p: str) -> str:
    pp = PurePosixPath(p)
    if pp.is_absolute():
        pp = PurePosixPath(*pp.parts[1:])
    return str(pp)
