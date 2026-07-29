# yakoon — Launcher for the Yakoon Platform

This is the only component distributed via PyPI. It ensures the default
Yakoon application (`y5n-apps-yak`) is installed, then forwards all
commands to it.

Everything else — the CLI, runtime, packs, apps — ships via Yakoon's
own distribution pipeline (repositories).

## Publish a new version to PyPI

```bash
cd launcher/y5n-launcher

# 1. Update version in pyproject.toml
# 2. Build:
python -m build

# 3. Upload to PyPI (username MUST be __token__):
python -m twine upload \
    --username __token__ \
    --password pypi-your-token-here \
    dist/yakoon-<version>*

# 4. Tag the release:
git tag launcher-v<version>
git push origin launcher-v<version>
```

Requires: `pip install build twine` and a PyPI API token.
The username is literally the string `__token__` (with underscores),
not your PyPI username. Create a token at https://pypi.org/manage/account/token/

## Development

```bash
pip install -e launcher/y5n-launcher
```

See https://github.com/yakoon-runtime/yakoon for the full source.
