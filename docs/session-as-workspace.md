# Session als Arbeitskontext

## Kernidee

Session ist kein technischer Container, der mit dem Client lebt und stirbt.
Session ist ein **Arbeitskontext**: benannt, besitzbar, joinbar, persistent.

```
Runtime
 └─ Session "research"
      owner=stefan
      flows=1
      clients=0   ← Laptop zugeklappt, Arbeit läuft weiter
```

## Lebenszyklus

```
Session entsteht (erster Client oder explizit)
  ↓
Arbeit passiert (flows, jobs, agents)
  ↓
Clients kommen und gehen
  ↓
Session bleibt (wenn flows laufen)
  ↓
Session stirbt (keine flows, keine clients)
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

| owner | Verhalten |
|---|---|
| `None` | öffentlich — jeder darf joinen |
| `stefan` | nur stefan darf joinen |
| `[stefan, anna]` | beide dürfen joinen |

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

Eine Connection kann mehrere Sessions abonniert haben, aber nur eine ist aktiv.

## Perspektive

Session als first-class Resource ermöglicht:
- **Kollaboration**: mehrere Clients in einer Session
- **Mobilität**: Laptop zu → Session bleibt → Laptop auf → session join research
- **Agenten**: Agent läuft in Session, mensch kann joinen und beobachten
- **Workspace**: Session = tmux-Session, aber runtime-native

## Session vs Historie

Eine Session lebt, solange sie Besitzer (homes), Beobachter (clients) oder
Arbeit (flows) hat. Sobald alle drei auf Null sind, wird sie gelöscht:

```
homes=0   clients=0   flows=0   →   cleanup
```

Das ist korrekt, weil **Historie nicht in der Session lebt**. Ein abgeschlossener
Flow schreibt vor dem Ende seinen `FlowRecord` in einen persistenten Store.
Die Session selbst ist transient — ihr Verschwinden löscht keine Information.

```
Runtime
 ├─ Sessions        (transient, lebt nur mit Arbeit/Beobachtern)
 ├─ Flows           (lebend, laufen in Sessions)
 └─ HistoryStore    (persistent, FlowRecords nach Abschluss)
```

Damit darf `_maybe_cleanup()` gnadenlos bleiben: sobald eine Session keine
Besitzer, Beobachter oder Arbeit mehr hat, ist sie nur noch Speicher —
und wird geräumt.
