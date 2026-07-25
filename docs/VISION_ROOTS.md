# Yakoon — Runtime Host Vision

## Kern-Erkenntnis

Der **Scheduler ist der Kernel**, nicht der Executor.

Ein **Host ist ein Runtime-Command**, kein Executor. Der Scheduler startet immer einen Host. Der Host entscheidet, wie das User-Programm eingebettet wird.

## Architektur-Schichten

```
Scheduler (Kernel)
   │
   └── Flow (immer ein Host)
         │
         └── Host-Node (z.B. /boot/python-host)
               │
               └── User-Programm (Script oder Command)
```

**Der Scheduler kennt keine Executor-Klassen mehr.** Er macht nur `FlowCursor.next()` auf einen Host. Der Host ist selbst ein ganz normaler Runtime-Command mit `_yak/run/app.py` und `async def run(space)`.

## Hosts sind installierbar

```
/boot/
  python-host/      → lädt .py oder _yak/run/app.py
  ruby-host/        → ruby app.rb
  bash-host/        → bash app.sh
  docker-host/      → docker run ...
  ssh-host/         → ssh user@host python app.py
```

Jeder Host ist ein Node. Kein Executor-Code, keine Registry, keine Sonderfälle.

## Host erkennt zwei Modi

1. **Command** (`_yak/run/app.py` mit `main()` oder `async main()`)
2. **Script** (bare `.py` — Top-Level-Code + optional `main()`)

Der Unterschied zwischen "Script" und "Command" verschwindet. Ein Command ist ein Spezialfall eines Skripts.

## Dualer Port-Proxy

`from y5n.sdk import ports` — der Proxy erkennt async/sync-Kontext:

| Kontext | `hello.greet()` gibt zurück | Aufrufer muss |
|---------|----------------------------|---------------|
| sync (kein Event-Loop) | Wert (str, int, …) | — |
| async (Event-Loop läuft) | Coroutine | `await` |

Gleiche SDK, kein API-Unterschied. Entwickler schreiben `await` wenn sie async sind.

## Konsequenz: Executor-Begriff stirbt

Heute:

```
Scheduler → Executor → Command
```

Morgen:

```
Scheduler → Host (Runtime-Command) → User-Programm
```

Der Scheduler kennt keine Executor-Klassen, kein `ExecutorKind`, keine `ExecutorRegistry`.
Alles sind Nodes. Yakoon benutzt Yakoon.

## Status

| Schritt | Was | Status |
|---------|-----|--------|
| 1 | Runtime Bus (Call/Response) | ✅ |
| 2 | Resolver | ✅ |
| 3 | SDK (`ports`, `context`) | ✅ |
| 4 | DirectTransport | ✅ |
| 5 | `/boot/python-host` (Spike) | ✅ |
| 6 | Tree-Routing (`host: python` → `/boot/python-host`) | 🔜 |
| 7 | Alte Executor-Klassen entfernen | 🔜 |
| 8 | Alte API (`run(space)` → `main()`) | 🔜 |
