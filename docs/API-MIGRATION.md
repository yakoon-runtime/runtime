# y5n.api Migration — Status

## Aktueller Stand

| Package | y5n.base / y5n.runtime | y5n.api | y5nstore |
|---------|------------------------|---------|----------|
| **y5nspace-shell** | **0** | alle | 0 |
| **y5nspace-runtime** | **0** | alle | 0 |
| **y5nspace-ident** | **0** | alle | **12** |

## Erledigt

| Schritt | api-Namespace |
|---------|---------------|
| `ModuleExport, ModuleMeta` | `y5n.api.modules` ✅ |
| `Invocation` | `y5n.api.invocations` ✅ |
| `Node, NodeScope, NodeSpace, Request` | `y5n.api.nodes` ✅ |
| `out`, `delay`, `receive`, … | `y5n.api.dsl` ✅ |
| `Projection`, `to_text` | `y5n.api.projections` ✅ |
| `ResourceRef` | `y5n.api.resources` ✅ |
| `Key, Namespace` | `y5n.api.naming` ✅ |
| `Permission`, `PermissionSet` | `y5n.api.permissions` ✅ |
| `OnAuthenticate`, `OnSessionSave`, `OnProjectionResolve`, `OnNewPermissionSet`, `OnParsePermissionSpec` | `y5n.api.ports` ✅ |
| `AuthResult` | `y5n.api.ports.models` ✅ |
| `DomainError` | entfernt (obsolet) ✅ |
| `Session` | `y5n.base.runtime.sessions` — Zyklus gelöst ✅ |

## Noch offen

| Fehlt | Dateien |
|-------|---------|
| `y5nstore.*`  (GetResult, IndexSpec, StorageSettings, build_store) | **12** (ident: models, services, setup, settings) |

## Bemerkungen

- `y5nstore` ist ein separates Paket (`y5nstore-event`). Eine Fassade in `y5n.api.store` oder als Port (`OnBuildStore` etc.) würde die letzte Kopplung von Spaces an ein konkretes Store-Backend kappen.
- `y5n.runtime.flow.Flow` in `y5nspace-runtime` ist kein Space-Code, sondern runtime-intern. Keine Migration nötig.
