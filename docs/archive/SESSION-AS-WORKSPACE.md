# Session as Workspace

## Core Idea

Session is not a technical container that lives and dies with the client.
Session is a **workspace context**: named, ownable, joinable, persistent.

```
Runtime
 └─ Session "research"
      owner=stefan
      flows=1
      clients=0   ← laptop closed, work continues
```

## Lifecycle

```
Session created (first client or explicit)
  ↓
Work happens (flows, jobs, agents)
  ↓
Clients come and go
  ↓
Session remains (if flows are running)
  ↓
Session ends (no flows, no clients)
```

## Naming

```
session create --name research --public
  → session "research"  (Key: system/session/research)
```

```
session list

  research       owner=stefan    flows=1   clients=0
  anonymous-12   owner=-         flows=0   clients=2
  customer-sync  owner=anna      flows=2   clients=0
```

## Ownership & Access

| owner | Behavior |
|---|---|
| `None` | public — anyone may join |
| `stefan` | only stefan may join |
| `[stefan, anna]` | both may join |

## Attach / Detach / Focus

```
session --attach <key>
  → Connection subscribed to session (observes projections)
  → Session is set as active (input goes here)
  → Old session remains subscribed

session --detach
  → Returns to home session (the session created at connect time)
  → Target session is unsubscribed, home becomes active again

session --list
  → All active sessions displayed with client/homes/flows counts
```

A connection always has exactly one active session. The **home session** is the connection's "personal workspace" created at connect time. `--attach` visits another session; `--detach` returns home. This is analogous to `git checkout` — switching branches doesn't delete your working directory.

A connection may subscribe to multiple sessions, but only one is active.

## Perspective

Session as a first-class resource enables:
- **Collaboration**: multiple clients in one session
- **Mobility**: laptop off → session stays → laptop on → session join research
- **Agents**: agent runs in session, human can join and observe
- **Workspace**: session = tmux session, but runtime-native

## Session vs History

A session lives as long as it has owners (homes), observers (clients), or work (flows). Once all three are zero, it is cleaned up:

```
homes=0   clients=0   flows=0   →   cleanup
```

This is correct because **history does not live in the session**. A completed flow writes its `FlowRecord` to a persistent store before ending. The session itself is transient — its disappearance does not delete information.

```
Runtime
 ├─ Sessions        (transient, lives only with work/observers)
 ├─ Flows           (alive, run in sessions)
 └─ HistoryStore    (persistent, FlowRecords after completion)
```

Thus `_maybe_cleanup()` can remain ruthless: once a session has no owners, observers, or work, it is just memory — and is freed.
