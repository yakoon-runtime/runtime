# ADR 7: Context as Root Provider

**Status:** Draft for discussion

## Context

The monorepo is a default, not an assumption. Yakoon components should
be discoverable through the Context, not through hardcoded paths.

## Principle

> **Das Monorepo sollte keine Sonderbehandlung sein. Es sollte lediglich der Default-Context sein.**

## Architecture

```
CLI
 │
 ▼
Context.current()
 │
 ▼
FileRepository(ctx.roots)
DirectoryArtifactStore(ctx.roots)
 │
 ▼
Repository roots: [./packs, ./runtime, ./apps, ./sdk, ...]
```

The Context becomes the central configuration unit. It answers:

> "Which roots are relevant for my current development environment?"

## Decision

### 1. Context carries `roots`

`.yak/context.toml` gains an optional `roots` section:

```toml
[context]
name = "yakoon"

[roots]
dirs = [
    "packs",
    "runtime",
    "apps",
    "sdk",
]
```

A standalone product repo:

```toml
[context]
name = "crm"

[roots]
dirs = ["."]
```

A workspace combining multiple repos:

```toml
[context]
name = "workspace"

[roots]
dirs = [
    "../yakoon/runtime",
    "../yakoon/sdk",
    "../crm",
    "../luma",
]
```

### 2. `_build_manager()` becomes context-based

```python
def _build_manager():
    ctx = Context.current()  # loads from .yak/context.toml
    
    # Roots from context, or monorepo fallback
    roots = ctx.roots if ctx and ctx.roots else _detect_monorepo()
    
    artifact_dir = Path(__file__).resolve().parents[8] / "apps" / "y5n-apps-yak" / "artifacts"
    
    repo = FileRepository(*roots, builtin_artifacts=artifact_dir)
    store = DirectoryArtifactStore(*roots)
    return InstallationManager(repo, store)
```

### 3. Context discovery

`Context.current()` walks up from CWD looking for `.yak/context.toml`.
This already exists as `find_context_root()` — it just needs a richer
data model.

```python
@dataclass
class Context:
    name: str
    roots: list[Path]
```

### 4. FileRepository and DirectoryArtifactStore

Both already accept `*roots`. No changes needed. They search all roots
for matching artifacts.

## Consequences

### Benefits
- Monorepo is just the default — products in their own repos work identically
- `_build_manager()` no longer knows about directory layouts
- Workspaces can combine multiple repos
- No architectural difference between "core" and "product" components

### Trade-offs
- `context.toml` format needs a version/schema field
- Existing contexts without `roots` fall back to monorepo detection
- `_detect_monorepo()` stays as a compatibility shim

### Non-goals
- This ADR does not change the Launcher. The Launcher never sees roots.
- This ADR does not change how artifacts are resolved (already flexible).
- This ADR only changes where roots come from.
