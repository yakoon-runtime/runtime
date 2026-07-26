# ADR 5: Artifact Repository

**Status:** Accepted (2026-07-26)

## Context

Artifacts need to be shareable between developers. The local `~/.yak/artifacts/`
works within a team that shares a filesystem, but not across the internet.

## Decision

1. **Yakoon does not host a registry.** Registries are existing infrastructure
   (GitHub Releases, S3, HTTP servers). Yakoon implements clients, not servers.

2. **ArtifactSource is renamed to `Repository`.** A Repository answers one
   question: "Do you know artifact X?" The concept is user-facing, like Git
   remotes.

3. **`_collect_roots` becomes a list of Repository instances.** Not file paths.

4. **GitHub Releases is the first remote Repository.**

5. **Cache is content-addressed by fingerprint.** `~/.yak/cache/github/<repo>/<fingerprint>/`

6. **Sources can be declared in environment.yml** for persistent configuration.

## Consequences

Positive:
- `install` and `sync` remain unchanged — they iterate Repositories
- Adding S3, HTTP, or a private registry is another Repository implementation
- GitHub Releases require no server-side infrastructure

Negative:
- Requires GitHub API access (rate limits apply to unauthenticated requests)
- Large artifacts benefit from GitHub's CDN, but initial download is unbuffered
