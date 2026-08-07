# ADR 15: Permissions Are Granted to Accounts on Runtime Paths

**Status:** Proposed — experiment branch (`experiment/permissions`);
production migration follows.

> **Permissions are granted to Accounts on runtime paths.**
>
> Yakoon has exactly one identity: the **Account**. An account optionally
> carries profile information. Everything else — groups, grants, elevation —
> is an attribute of that identity. There is no second identity concept.

## Vocabulary

The ADR fixes two terms that the permissions experiment revealed:

> **Account** — the only security identity in a runtime: login, credentials,
> groups, grants.
>
> **Profil** — optional personal information an account may carry
> (`name`, `mail`, `language`, `avatar`). A bot account has none.

The distinction is not *User vs. Account*. It is *Account with profile* vs.
*Account without profile*. The term **User** is deliberately removed from
the security vocabulary — it reintroduces a second mental model.

## Context

The old model had no account. A `User` was simultaneously a person, a login,
and (for services) a technical identity — the Unix model. Groups were groups
of users. This works, but it is the Unix "system user" compromise:

```
stefan, www-data, postgres, daemon  → all "users"
```

- A bot is an account without a profile — no separate object, no half-identity.
- A person is an account with a profile.
- The permission check needs nothing about the person; it asks only
  *"may this account use this path with this operation?"*

Unix had the right user experience (one identity + groups + sudo) but a
flawed data model for non-human actors. Yakoon keeps the UX and repairs the
model.

## Problem

1. **Two identity concepts confuse the operator.** Managing "users" and
   "accounts" as equal admin concepts is the worst of both worlds.
2. **The runtime's permission check was dead code.** The tree built every
   node as `anonymous=True` (`tree.py`), so no command ever enforced a
   grant.
3. **The grant keys never matched the check keys.** The runtime checked
   `parent:child[.action]` (e.g. `users:list`), bootstrap granted the old
   `ident-app:user.list` scheme — no grant could ever match.
4. **No session ever received permissions.** `set_permissions()` was never
   called; after `su` the session held an empty `PermissionSet`.
5. **Elevation was modeled as a second identity.** "I am both user and
   admin" led to `stefan` + `stefan-admin` — two logins. The real need is
   *elevation within one identity* (sudo), not a second account.

## Decision

### 1. The Account is the only identity

```
Account
──────────────────────────────
username
credentials

profile?        ← optional (name, mail, language, avatar)

groups
grants
```

- **Identity**: Stefan, Scheduler, API, Backup, CRM-Bot — all are equal
  identities.
- **Profile**: what a person additionally owns; a bot has none.
- **Group**: a bundle of accounts that may itself carry grants.
- **Join**: account → group.
- **Grant**: set on an account or a group.

### 2. Permissions are granted on runtime paths

Grant keys are full node paths in the runtime tree:

```
/usr/bin/ls
/usr/sbin/ident/accounts
/opt/crm/contact/edit
```

Optional action suffix: `/opt/crm/contact/edit.version`. The engine knows
only the runtime tree — no app/command scheme. The engine builds the check
key from `node.path` (`InvocationResolver._ensure_invocation`).

### 3. Permissions are inherited along the runtime path hierarchy

> **Permissions are inherited along the runtime path hierarchy.**

- A grant on `/usr/bin` applies to `/usr/bin` and **all descendants**
  (segment-based: `/usr/bin/ls` matches, `/usr/binary` does not). No
  wildcards needed.
- The mount structure of the runtime tree thereby *becomes* the security
  model: a pack chooses where it lives by its mount path, and grants are
  placed exactly there (`admins → /usr/bin`, `ident-admins →
  /usr/sbin/ident`).
- Allow bits **accumulate** along the chain, deny bits are **subtracted**
  (`effective = union(allow) - union(deny)`). A deny removes only its own
  bits — a broader allow stays as the base. There is no "most specific
  wins" override.
- **Traversal is derived, not granted** (Decision 2026-08-07). Two graphs
  live in one tree: the *authorization graph* (what an account may use)
  and the *reachability graph* (how the runtime reaches it). Ancestor
  containers of an explicit grant are automatically discoverable — an
  explicitly allowed area is **always reachable**. Ancestor denies affect
  only functional rights, never the derived reachability of an explicitly
  allowed target. An explicit self-grant is reduced only by self-denies.
  This separates authorization ("may I?") from reachability ("how do I get
  there?").
- **Root is the top grant, not an exception** (Decision 2026-08-07). The
  `admins` group receives the hierarchically highest grant `/\|rwx`.
  Inheritance then covers the whole tree — "root" is merely what an account
  looks like from the outside when its grant begins at the root. No
  superuser flag, no bypass: the same mechanism as for any account. The
  name is irrelevant — only the grant position and the session security
  context matter.

### 4. A single bitset, deny stays

- One bitset per grant: `r`, `w`, `x` today; later `a` (administer),
  `d` (delegate) can be added. No `rwx:rwx` double scope — owner/group/other
  is not an axis here; account and group are already first-class entities.
- **The bits describe the operations possible on a node — not the node's
  type** (Decision 2026-08-07). The runtime tree will grow beyond commands:
  files, documents, databases, APIs, queues, models — all are nodes with the
  same bits. A command today uses mostly `x`; a file tomorrow uses `rw`; a
  document may later use `rwad`. `rwx` is deliberately NOT reduced to `x`:
  the bits are the general operations model of the runtime and grow with the
  system, without special rules per resource type.
- **Two levels: runtime operations vs. bits** (Decision 2026-08-07). The
  node type maps runtime operations onto bits:

  ```
  Container  DISCOVER -> r   (see + move)
  Command    READ -> r, EXECUTE -> x
  Document   READ -> r, WRITE -> w
  API        EXECUTE -> x
  Queue      READ -> r, WRITE -> w
  Database   READ -> r, WRITE -> w
  ```

  `cd` asks `check(path, DISCOVER)` — the container maps it to `r`. The
  permission system stays small (`rwx`) while the runtime grows: new node
  types only remap, they never need new bits. No Unix copying — `x`-on-
  directories is a historical compromise (search/traverse repurposed);
  navigation (`cd`/`ls`/`man`/`cat`) is a read operation, editing is
  `write`, command execution is `execute`.
- **Navigation is a runtime operation** (Decision 2026-08-07, replaces the
  earlier "visibility / filesystem" framing). `cd` and `ls` are not shell
  special cases — they are operations on a container node. Whether they are
  allowed is decided by the permission check for the operation
  (`DISCOVER`, `LIST`) and the node type's mapping to the permission bits.
  A runtime tree that will hold files, documents, databases and APIs makes
  navigation itself part of the permission model, not a bypass.
- **The node type needs no new `type:` marker.** `navigable` in `yak.yml`
  already says it: `navigable: true` → container, `navigable: false` → leaf
  (resource). A leaf may later declare `kind: command | document | database`
  for finer operation mapping — for navigation, `navigable` is enough.
- **Deny stays** (Decision 2026-08-06): deny grants subtract bits. A single
  account can be excluded from a group grant without changing membership.
  Fail-closed standard.
- **Deny subtracts only its bits** (Decision 2026-08-07): a
  `deny /usr/bin/shutdown|x` removes only `x` from the inherited
  `allow /usr/bin|rwx` — `r`/`w` remain. This keeps the bits meaningful as
  the primitive of the permission model.

### 5. Pipeline

```
Account
  ↓
PermissionResolver
  ↓
PermissionSet
  ↓
Elevation
  ↓
Execution
```

Four domains: **Identity → Authorization → Elevation → Execution**.

### 6. Elevation is a session security context, not a second identity

> **Permissions answer "may I?". The session security context answers "under which security mode?".**

Three domains, fully separate:

```text
Account  → Who am I?
Grant    → What may I do?
Session  → Under which security mode?  (security_context)
```

The session's `security_context` is **normal | temporary | administrative**.
It never carries rights — an administrative session has no power a normal
session lacks. It changes only the interaction mode: is the will question
asked again before a privileged invocation?

- **normal**: privileged invocations require elevation.
- **temporary**: the next privileged invocation runs, then the session
  falls back to normal — exactly one invocation, no TTL, no cache.
- **administrative**: a session consciously established as administrative
  (`su --administrative`) — privileged invocations run without repeated
  confirmation.

The **login is the will act**, the password is the confirmation. Therefore
`su --administrative` requires a password. Elevation does not come from the
identity: a normal session is asked at privileged operations, an
administrative session is not. The session context decides, not the name.

> **There is no root concept anymore.** `root` is merely the conventional
> demo account shipped with Yakoon (bootstrap seeds it with the top grant
> `/\|rwx`). Nothing in the runtime treats the name `root` specially —
> there are only accounts with grants, and sessions with a security
> context. `login root` (normal) is asked at privileged operations,
> `login root --administrative` is not — exactly like any other account.

> **An administrative session never holds rights. It changes only the interaction mode between user and runtime.**

`privileged: true` is an **invocation flag** (like `anonymous` describes
the entry, `privileged` describes the flow). The engine rebuilds the
pipeline automatically; the command knows nothing about it.

"Verification" is deliberately open: today a password (re-auth via `su`),
tomorrow passkey, FIDO2, MFA, hardware key, biometrics. The architecture
fixes a verification, not a secret.

### 7. Process boundary

The ident pack and the engine are separate processes (stdio/JSON). The
`PermissionResolver` therefore returns **spec strings** (e.g.
`/crm/contact/edit|rwx`, `-/ident/users|x`); the engine parses them into a
`PermissionSet` via `SessionAdapter.set_permissions`. No engine object
crosses the boundary.

### 8. The runtime declares permission enforcement

The tree reads `anonymous` from `yak.yml` (default `False`). Public/utility
nodes (`su`, `logout`, `err`) declare `anonymous: true` explicitly. All other
nodes are permission-enforcing — the check is real, not dead code.

## Consequences

### Benefits

- **One identity.** The operator manages accounts and groups; the person is
  an optional profile. No "user vs. account" cognitive load.
- **Bots are first-class.** A service is simply an account without a profile —
  the Unix system-user hack disappears.
- **The check works.** Every non-anonymous node enforces grants; the fq key
  is the node's full path, so grants and checks finally agree.
- **Elevation without identity change.** Privileged operations are activated
  by verification within the same identity — sudo, not `stefan-admin`.
- **Engine/ident separation.** The engine asks only "may this account use
  this path with this operation?"; the pack owns the sources (direct,
  group, later role).

### Trade-offs

- **"One person, several accounts"** (e.g. admin/readonly) means duplicated
  profiles. Accepted deliberately: one concept for the operator outweighs a
  profile-refactoring trick nobody understands.
- **Elevation adds a verification step** to privileged operations — the
  deliberate "admin moment" Unix introduced with sudo.

### Is the system simpler or more complex?

- **Model: simpler.** One identity instead of two. Grants on paths instead of
  two incompatible schemes.
- **Runtime: enabled, not bigger.** The enforcement path existed but was
  bypassed (`anonymous=True`); enabling it adds no machinery.
- **Operator: simpler.** Accounts + groups + elevation, exactly the Unix
  pattern that has carried since the 1960s — minus the system-user hack.

## Open questions

1. ~~Elevation semantics.~~ **Resolved (2026-08-07):** the elevation gate
   lives at the engine dispatch (`InvocationResolver._ensure_invocation`);
   `su --administrative` / `su --temporary` establish the session security
   context. The challenge is the login itself (password = will act).
2. ~~`privileged: true` vs. policy.~~ **Resolved (2026-08-07):** `privileged`
   is an invocation flag declared on the path, like `anonymous`. Elevation
   is deliberately not a policy decision in the minimal model — the path
   declares that a conscious confirmation is required on top of the grant.
3. **Challenge mechanism.** Today the challenge is password re-auth via
   `su --administrative`. The re-auth port is not yet pluggable (passkey,
   FIDO2, biometrics as alternative challenge mechanisms).
4. **`temporary` TTL.** `temporary` is deliberately implemented without TTL
   or cache (exactly one invocation). A `temporary(ttl=5m)` can be added
   later as a comfort feature without changing the model.

## Implementation sketch (for later)

**Done on the experiment branch:**

1. Engine fq → full node paths via `node.path` (`machine/resolver.py`).
2. `Permission`/`PermissionParser`/`PermissionSet`: single `bits`, scope2
   removed, deny kept (`runtime-api/permissions`, engine capabilities).
3. Join → account-to-group (`JoinData.account_key`, service, commands,
   index).
4. `AccountData`/`AccountService` completed: namespace, index, publish,
   `get_by_username`, `add_account`.
5. `PermissionResolver` account-based, publishes spec strings
   (`ident.permissions.resolver`).
6. Auth flow: `su`/`authenticate` → resolver → `session.set_permissions()`
   (new `SessionAdapter.set_permissions` parses specs → `PermissionSet`).
7. `grants user*` → `grants account*` (modules, structure, YDF docs).
8. Bootstrap: root account + admins group, grants on the real tree
   (`/usr/bin`, `/usr/sbin/ident`, `/opt`, `/dsl`).
9. `anonymous` read from yak.yml (default False); `su`/`logout`/`err`
   declare it.
10. User concept removed: profile fields on `AccountData`, `users` commands
    → `accounts` commands, `joins users` → `joins accounts`.
11. Path inheritance: `PermissionSet.check` walks the chain upward, allows
    accumulate, denies subtract. Tests in `test_permission_set.py`.
12. Grant vocabulary: `permission_key` → `path` (model, service, commands,
    structure, YDF docs). The grant is `path + bits + deny` — the operator
    grants access to a runtime path, not an abstract permission.
13. Experiment test `tests/test_permissions.py` (direct, group,
    deny subtraction).
14. Elevation: `privileged: bool` on `Node` (read from yak.yml), gate in
    `InvocationResolver._ensure_invocation` (ElevationRequired → err node),
    `security_context` on `SessionData`/`Session` (normal/temporary/
    administrative), `su --administrative` / `su --temporary` establish the
    context after password verification, logout resets it. Tests:
    `test_elevation.py`, `test_elevation_e2e.py`, `test_elevation_dispatch.py`,
    `test_privileged_node.py`, `test_ident_elevation.py`.
15. Root-Grant `/\|rwx`: bootstrap grants root/admins the hierarchically
    highest grant instead of individual mounts (`_root_grant_specs =
    [("/", "rwx")]`). `ls /` shows all mounts again.
16. Runtime operations: `Operation(READ, WRITE, EXECUTE)` in the API;
    `Node.required_bit(operation)` maps via `navigable` (container:
    READ→r/WRITE→w; leaf: READ→r/EXECUTE→x); `PermissionChecker.check`
    and the resolver enforce operations via node + operation instead of
    perm-key strings. Tests: `test_operations.py`.
17. cd/ls as READ: new `permissions` port (`PermissionAdapter.check(path,
    operation)`); `cd` rejects without READ on the target container, `ls`
    filters entries without READ. Only runtime nodes are protected —
    filesystem mounts (`~/home`) stay open. Tests:
    `test_permission_adapter.py`, `test_checker_wire.py`.
18. Traversal in `PermissionSet.check`: the path to one's own grants is
    automatically readable (segment-based). Stefan with a grant on
    `/usr/bin` sees `/usr` and `/` in `ls`, but not `/usr/sbin` or `/opt`.
    Tests: `test_permission_set.py`.

**Remaining / parked:**

1. ~~Remove the User concept~~ — **done**: profile fields on `AccountData`
   (`name`, `mail`, `language`), `UserData`/`UserService`/user namespace
   removed, `users` commands became `accounts` commands, `joins users`
   became `joins accounts`.
2. ~~Path inheritance~~ — **done**: grants inherit along the runtime path
   hierarchy; allows accumulate, denies subtract (Open question 3 resolved).
3. ~~Elevation~~ — **done**: privileged paths + verification (Open questions
   1–2 resolved); challenge mechanism still password-only, not yet pluggable.
4. Process-level end-to-end: real `su` session → visible `PermissionDenied`.
