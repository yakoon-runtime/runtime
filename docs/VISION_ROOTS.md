# Yakoon — Runtime Host Vision

## Kern-Erkenntnis

Der **Scheduler ist der Kernel**, nicht der Executor.

Alles andere sind Hosts — unterschiedliche Lebensmodelle auf demselben Kernel.

## Architektur

```
Scheduler (Kernel)
   |
   |── Runtime Host     async def main()     — persistent, Coroutine
   |── Batch Host       def main()           — einmal, synchron
   |── Process Host     _yak/run/app (exec)  — externer Prozess
   |
   alle nutzen:
   from y5n.sdk import ports, context
```

## Lebensmodelle

| Host | Lebensdauer | API | Beispiel |
|------|-------------|-----|----------|
| Runtime | persistent im Scheduler | `async def main()` | Services, Daemons, interaktive Commands |
| Batch | einmalig | `def main()` | CLI-Skripte, Migrationen, Tests |
| Process | externer Prozess | `#!/usr/bin/env bash` | Fremdsprachen, Legacy |

## API-Prinzipien

1. **`NodeSpace` verschwindet aus der öffentlichen API.** Kein `space.ports`, kein `space.request`.
2. **Commands nutzen ausschliesslich `y5n.sdk`.** `ports.get()`, `context.current()`, `context.request()`.
3. **`print()` ist der standard Output.** Der Host mapped stdout auf den Outcome-Stream.
4. **`await context.wait()` erlaubt Schlafen.** Der Flow bleibt im Scheduler, blockiert nicht.

## Migration

| Schritt | Was | Status |
|---------|-----|--------|
| 1 | Runtime Bus (Call/Response) | ✅ aus `transport-abi` |
| 2 | Resolver | ✅ aus `transport-abi` |
| 3 | SDK (`ports`, `context`) | ✅ aus `transport-abi` |
| 4 | DirectTransport | ✅ aus `transport-abi` |
| 5 | Runtime Host (ohne NodeSpace) | 🔜 neu |
| 6 | Batch Host (ohne ThreadPool) | 🔜 aus python.py |
| 7 | Alte API (`run(space)`) entfernen | 🔜 |

## Historischer Kontext

Der `experiment/transport-abi` Branch hat bewiesen:

- Eine sprachneutrale SDK + Runtime Bus funktionieren
- `print()` kann auf Outcome-Stream abgebildet werden
- Der ThreadPool-Ansatz war ein Prototyp, kein Produktionsziel

Der `experiment/runtime-host` Branch baut darauf auf:

- Der Scheduler bleibt der Kernel
- Seine API wird ersetzt, nicht er selbst
- Hosts werden nach Lebensmodell unterschieden, nicht nach Sprache
