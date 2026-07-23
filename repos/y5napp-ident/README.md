# y5napp-ident

*Identity and permission management for Yakoon.*

This package provides user administration, group management,
permission grants, and authentication services.

## Commands

| Command | Module | Description |
|---------|--------|-------------|
| `su` | `y5n.apps.ident.su` | Switch user |
| `users add` | `y5n.apps.ident.apps.users.add` | Create a user |
| `users list` | `y5n.apps.ident.apps.users.list` | List users |
| `users edit` | `y5n.apps.ident.apps.users.edit` | Modify a user |
| `users delete` | `y5n.apps.ident.apps.users.delete` | Remove a user |
| `groups add` | `y5n.apps.ident.apps.groups.add` | Create a group |
| `groups list` | `y5n.apps.ident.apps.groups.list` | List groups |
| `groups edit` | `y5n.apps.ident.apps.groups.edit` | Modify a group |
| `groups delete` | `y5n.apps.ident.apps.groups.delete` | Remove a group |
| `joins add` | `y5n.apps.ident.apps.joins.add` | Add user to group |
| `joins remove` | `y5n.apps.ident.apps.joins.remove` | Remove user from group |
| `joins groups` | `y5n.apps.ident.apps.joins.groups` | List groups for a user |
| `joins users` | `y5n.apps.ident.apps.joins.users` | List users in a group |
| `grants user add` | `y5n.apps.ident.apps.grants.user_add` | Grant permission to user |
| `grants user remove` | `y5n.apps.ident.apps.grants.user_remove` | Revoke permission from user |
| `grants user show` | `y5n.apps.ident.apps.grants.user_show` | Show user permissions |
| `grants group add` | `y5n.apps.ident.apps.grants.group_add` | Grant permission to group |
| `grants group remove` | `y5n.apps.ident.apps.grants.group_remove` | Revoke permission from group |
| `grants group show` | `y5n.apps.ident.apps.grants.group_show` | Show group permissions |
| `grants perm show` | `y5n.apps.ident.apps.grants.perm_show` | Show all permissions |

## Services

The package also provides backend services used by the runtime:

- **AccountService** — user creation, lookup, password verification
- **AuthenticationService** — credential validation, session auth
- **GroupService** — group CRUD
- **JoinService** — user-group membership
- **PermissionGrantService** — permission grants
- **Resolver** — user/group resolution by key
- **Verifier** — password policy enforcement

## Setup

On first start, `bootstrap.py` creates the default admin account
and initial permission set.
