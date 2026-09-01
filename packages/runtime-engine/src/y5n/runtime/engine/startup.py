"""Session startup declaration (ADR-25).

The installation may declare a Session Startup Sequence: an ordered
sequence of ordinary command invocations executed when a new Session
is created. This module loads the declaration only — the sequence is
data, nothing here executes it.

```yaml
# .yak/startup.yml
startup:
  - welcome
```

Loading follows the installation-file conventions: an absent file
declares no startup and invalid entries are skipped, not raised.
Whether an item may run remains Structure's decision at invocation
time — startup determines execution and order, structure determines
authorization.
"""

from __future__ import annotations

from pathlib import Path

import yaml


def load_startup(path: Path) -> tuple[str, ...]:
    """Load the installation's startup sequence, or () when none declared.

    A missing file, an empty document, a missing or empty ``startup``
    key, or a non-sequence ``startup`` value all declare no startup.
    Items keep their declaration order; only non-empty strings are kept.
    """
    if not path.is_file():
        return ()
    with open(path) as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        return ()

    raw = data.get("startup")
    if not isinstance(raw, list):
        return ()
    return tuple(item for item in raw if isinstance(item, str) and item)
