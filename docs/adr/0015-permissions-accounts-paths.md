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

### 4. A single bitset, deny stays

- One bitset per grant: `r`, `w`, `x` today; later `a` (administer),
  `d` (delegate) can be added. No `rwx:rwx` double scope — owner/group/other
  is not an axis here; account and group are already first-class entities.
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

### 6. Elevation, not a second identity

> **Elevation activates privileged operations after successful verification.**

Stefan stays Stefan. To run a privileged operation (`users delete peter`),
the system asks for verification — he never becomes `stefan-admin`.
Authorization comes from the group; activation requires verification.

"Verification" is deliberately open: today a password, tomorrow passkey,
FIDO2, MFA, hardware key, biometrics. The architecture fixes a verification,
not a secret.

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

1. **Elevation semantics.** Where is verification requested — at the engine
   dispatch, or inside the command (sudo-style wrapper)? Not decided.
2. **`privileged: true` vs. policy.** Whether a path *requires* elevation may
   be a security-policy decision rather than a path declaration. The runtime
   should know only that a path *can* require elevation; whether it does may
   be policy. Open.

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
12. Experiment test `tests/test_permissions_experiment.py` (direct, group,
    deny subtraction).

**Remaining / parked:**

1. ~~Remove the User concept~~ — **done**: profile fields on `AccountData`
   (`name`, `mail`, `language`), `UserData`/`UserService`/user namespace
   removed, `users` commands became `accounts` commands, `joins users`
   became `joins accounts`.
2. ~~Path inheritance~~ — **done**: grants inherit along the runtime path
   hierarchy; allows accumulate, denies subtract (Open question 3 resolved).
3. Elevation: privileged paths + verification (Open questions 1–2).
4. Process-level end-to-end: real `su` session → visible `PermissionDenied`.
