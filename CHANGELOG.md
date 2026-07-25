# Changelog

## Unreleased

- Initial open-source release preparation
- Documentation restructuring: 57 → 5 active docs
- All docs translated to English

## 2026-07-17 — Language-Neutral Integration Platform

First proof that Yakoon is a language-neutral runtime platform:

- **`entry.run`** replaces `_yak/run/` convention — the developer decides
  where the executable lives, not the platform
- **`expose`** field makes every package manifest self-describing
- **Yak-Package-Rule** uses tree knowledge (not filesystem heuristics)
  to show only Yak objects inside packages
- **`.NET process host`** (`/boot/dotnet/process`) executes compiled
  .NET assemblies via `dotnet <dll>` — zero changes to the runtime core
- **Python hosts** (`runtime`, `thread`, `process`) fully operational
- **All ~100 commands** across `yakoon-root`, `yakoon-crm`, and
  `yakoon-luma` migrated to the flat `_yak/` structure with `libs/`
  pattern for shared infrastructure
