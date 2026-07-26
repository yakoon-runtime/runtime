# Artifact

An artifact is a language-neutral build output.

## Format

```
<name>-<version>.<builder>.artifact/
    artifact.yml       Manifest
    package.whl        (or package.dll, package.jar, ...)
```

## Manifest

```yaml
name: y5n-packs-hello
version: 0.1.0
kind: package
host: python
builder: python
fingerprint: sha256:abc123...
```

## Sources

Artifacts are resolved from multiple sources, in order:

1. `.yak/artifacts/` (context-local, from `build`)
2. `~/.yak/artifacts/` (user-global, from `publish`)
3. `~/.yak/cache/` (shared pre-built)

## Language independence

The `artifact.yml` manifest tracks the builder and host,
not the implementation language. This allows a single platform
to manage Python wheels, .NET assemblies, JARs, and native
binaries with the same tooling.
