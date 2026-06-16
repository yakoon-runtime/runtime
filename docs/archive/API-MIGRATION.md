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
| `Flow` (Protocol) | `y5n.api.flow` (neu) ✅ |

## Keine Migration geplant

| Paket | Begründung |
|-------|------------|
| `y5nstore.*` (12 Dateien in ident) | **Bewusste Abhängigkeit.** y5nstore ist eine konkrete Datenbank-Bibliothek, die ident für seine Daten wählt. Anders als bei `PermissionSet`/`PermissionParser` hat die Runtime keine Hoheit über die Speicherung — jeder Space darf sein eigenes Backend wählen. Ein generischer Port würde Typdetails nur verschieben, nicht eliminieren. |
| `y5n.runtime.flow.Flow` (2 Dateien in y5nspace-runtime) | **Runtime-intern.** Kein Space-Code, sondern Infrastruktur innerhalb der Runtime. |

## Abgeschlossen

**Alle drei Spaces haben 0 Imports aus `y5n.base` oder `y5n.runtime`.** Jeder Import geht durch `y5n.api.*` oder ist eine bewusste, nicht abstrahierte Abhängigkeit.
