# y5n.api Migration — Fehlende Oberflächen

Stand nach Migration der `y5n.api`-kompatiblen Imports in `y5nspace-ident`.

## Status

| Package | y5n.base | y5n.api | y5nstore |
|---------|----------|---------|----------|
| y5nspace-ident | **18 Dateien** (nur nicht-migrierbare) | **22 Dateien** (soeben umgestellt) | 12 Dateien |
| y5nspace-runtime | **0 Dateien** | alle | 0 |
| y5nspace-shell | **0 Dateien** | alle | 0 |

## Fehlende y5n.api-Oberflächen (nach Priorität)

### 1. `y5n.base.naming` → `y5n.api.naming` ✅ erledigt

Erstellt unter `y5n/api/naming.py`, 34 Dateien umgestellt.

### 2. `y5n.base.runtime.errors` → `y5n.api.errors` (7 Dateien)

| Symbol | Verwendung |
|--------|-----------|
| `DomainError` | grant/setup.py, grant/grant_group.py, grant/grant_user.py, member/membership_add.py, member/membership_remove.py, member/membership_groups.py, member/membership_users.py |

**Vorschlag:** `y5n.api.errors`
```python
from y5n.api.errors import DomainError
```

### 3. `y5n.base.plugins.models` → `y5n.api.models` (2 Dateien)

| Symbol | Verwendung |
|--------|-----------|
| `AuthResult` | runtime/su.py, services/authentication.py |

**Vorschlag:** `y5n.api.models`
```python
from y5n.api.models import AuthResult
```

### 4. `y5n.base.plugins.ports.OnAuthenticate` → `y5n.api.ports` (2 Dateien)

`OnAuthenticate` ist der einzige Port aus `y5n.base.plugins.ports`, der noch nicht in `y5n.api.ports` exportiert wird (OnSessionSave, OnProjectionResolve etc. sind bereits dort).

**Vorschlag:** In `y5n.api.ports` aufnehmen:
```python
from y5n.base.plugins.ports import (
    ...
    OnAuthenticate,
)
```

### 5. `y5n.runtime.capabilities.permission` → `y5n.api.permissions` (2 Dateien)

| Symbol | Verwendung |
|--------|-----------|
| `PermissionParser` | runtime/setup.py |
| `Permission`, `PermissionSet` | services/resolver.py |

**Vorschlag:** `y5n.api.permissions`
```python
from y5n.api.permissions import PermissionParser, Permission, PermissionSet
```

### 6. `y5nstore.event.*` → `y5n.api.store` (12 Dateien, niedrigste Priorität)

| Symbol | Verwendung |
|--------|-----------|
| `GetResult` | models (5×) |
| `GetResult, IndexKey, IndexSpec, IndexTerm, IndexValue, JsonValue, PutResult, SnapshotHint, ValueType` | services (5×) |
| `StorageSettings` | settings/__init__.py |
| `build_store` | runtime/setup.py |

**Vorschlag (optional):** `y5n.api.store` als Fassade. Niedrige Priorität, da y5nstore eine eigene Domain ist.
