# y5n.api Migration — Status

## Aktueller Stand

| Package | y5n.base | y5n.api | y5n.runtime | y5nstore |
|---------|----------|---------|-------------|----------|
| **y5nspace-shell** | **0** | alle | 0 | 0 |
| **y5nspace-runtime** | **0** | alle | 2 (`y5n.runtime.flow`) | 0 |
| **y5nspace-ident** | **0** | alle | **2** (`y5n.runtime.capabilities.permission`) | **12** |

## Erledigt

| Schritt | api-Namespace | Dateien |
|---------|---------------|---------|
| `ModuleExport, ModuleMeta` | `y5n.api.modules` ✅ | 1 |
| `Invocation` | `y5n.api.invocations` ✅ | 5 |
| `Node, NodeScope, NodeSpace, Request` | `y5n.api.nodes` ✅ | >30 |
| `out` | `y5n.api.dsl` ✅ | 14 |
| `Projection` | `y5n.api.projections` ✅ | 2 |
| `ResourceRef` | `y5n.api.resources` ✅ | 2 |
| `Key, Namespace` | `y5n.api.naming` ✅ | 34 |
| `OnProjectionResolve, OnSessionSave, OnAuthenticate` | `y5n.api.ports` ✅ | 4 |
| `AuthResult` | `y5n.api.ports.models` ✅ | 2 |
| `DomainError` | entfernt (obsolet) | 7 |

## Noch offen

| Fehlt | Vorschlag | Dateien |
|-------|-----------|---------|
| `PermissionParser, Permission, PermissionSet` | `y5n.api.permissions` | 2 |
| `y5nstore.*` (GetResult, IndexSpec, …) | `y5n.api.store` (optional) | 12 |
| `Flow` (y5nspace-runtime) | `y5n.api.flow` | 2 |

## Bemerkungen

- `y5nstore` ist ein separates Paket — eine Fassade in `y5n.api.store` ist optional, senkt aber die Kopplung.
- `y5n.runtime.flow.Flow` wird in `y5nspace-runtime` (runtime, nicht Space-Logik) verwendet. Migration zu `y5n.api` wäre möglich, aber niedrige Priorität, da es kein Space-Code ist.
