# Changelog

## Unreleased

- **`_yak/` → `.yak/`** — renamed all bundle metadata directories for consistency with `.yak/` manager directory
- **`Mount` refactored** — `pack` → `source` (absoluter Pfad). `environment.yml` speichert nur noch `source` + `target`, keine Herkunft mehr
- **`sync` vereinfacht** — `_discover_packs` → `_discover_mounts`. Sync materialisiert nur noch `list[Mount]`, kennt keine Packs/Install mehr
- **`materializer` entkoppelt** — braucht kein `ArtifactStore` mehr, bekommt `Mount.source` direkt als Pfad
- **`resolver` fokussiert** — gibt nur noch `(packs, tools)` zurück, keine Mounts mehr
- **`yak mount add/remove/list`** — neues Command-Family für User-Mounts mit auto-sync
- **Bugfix: `installer.py` dead code** — `if projects:` stand nach `return` in `_find_tool()`, jetzt am Ende von `install()`
- Initial open-source release preparation
- Documentation restructuring: 57 → 5 active docs
- All docs translated to English

## 2026-07-17 — Language-Neutral Integration Platform

First proof that Yakoon is a language-neutral runtime platform:

- **`entry.run`** replaces `.yak/run/` convention — the developer decides
  where the executable lives, not the platform
- **`expose`** field makes every package manifest self-describing
- **Yak-Package-Rule** uses tree knowledge (not filesystem heuristics)
  to show only Yak objects inside packages
- **`.NET process host`** (`/boot/dotnet/process`) executes compiled
  .NET assemblies via `dotnet <dll>` — zero changes to the runtime core
- **Python hosts** (`runtime`, `thread`, `process`) fully operational
- **All ~100 commands** across `yakoon-root`, `yakoon-crm`, and
   `yakoon-luma` migrated to the flat `.yak/` structure with `libs/`
  pattern for shared infrastructure
