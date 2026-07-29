# Roadmap

## Phase A ✅ — Core hardening
## Phase B ✅ — Distribution  
## Phase C ✅ — Launcher (Self-hosting)
## Phase D 🚧 — Platform completion

### D.1 Repository auto-discovery ✅
- `[repositories] sources` in context.toml
- `install` and `sync` read them automatically

### D.2 RepositoryResolver (planned)
- Unified resolution: Context → CLI → Defaults
- Replaces ad-hoc source collection

### D.3 Builder protocol (future)
- PythonBuilder exists, Go/.NET/Java builders follow
- Language-neutral artifacts already supported

### D.4 Repository protocol (future)
- FileRepository + GitHubReleaseRepository exist
- GitLab, S3, OCI follow the same interface

## Phase E 🌱 — Ecosystem

The first independent product outside the monorepo.
For example: `github.com/yakoon-runtime/hello`

Goal: validate that the platform works for external developers
who know nothing about Yakoon's internal structure.

```bash
git clone https://github.com/yakoon-runtime/hello
cd hello
yak init
yak create pack hello
...
yak build
yak publish --repository github:yakoon-runtime/hello --release

# Any user:
mkdir test && cd test
yak init
echo '[repositories]' >> .yak/context.toml
echo 'sources = ["github:yakoon-runtime/hello"]' >> .yak/context.toml
yak install y5n-packs-hello
yak sync
yak shell
```

If this works without modifying the platform, the architecture is complete.
