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

## Phase E 🌱 — Ecosystem validation

### TODO: First external product

Extract a product from the monorepo into its own repository.
Validate that the full lifecycle works without platform changes.

Candidate repositories (one per product):

```
github.com/yakoon-runtime/hello     ← simple test
github.com/yakoon-runtime/crm       ← real product
github.com/yakoon-runtime/luma      ← real product
```

Expected flow:

```bash
git clone github.com/yakoon-runtime/hello
cd hello
yak init
yak create pack hello
yak build
yak publish --repository github:yakoon-runtime/hello --release

# Any user on any machine:
mkdir test && cd test
yak init
echo '[repositories]
sources = ["github:yakoon-runtime/hello"]' >> .yak/context.toml
yak install y5n-packs-hello
yak sync
yak shell
# hello command available
```

Success criterion: no platform code changes needed.
If changes are needed, those changes are the real Phase D work.
