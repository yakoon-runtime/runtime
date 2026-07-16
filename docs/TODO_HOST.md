# Host-Architektur — Nächste Schritte

Stand: 16.07.2026, `experiment/runtime-host`

## ✅ Erreicht

- `/boot/python/`-Struktur mit `_shared.py` + `runtime/thread/process/`
- Host-Delegation via `_make_host_handler()` — Engine weiss nichts von Hosts
- `host: /boot/python/runtime` in yak.yml — voller Pfad, kein Short-Name
- SDK mit dualem Proxy (sync/async)
- Runtime Bus, Resolver, DirectTransport

## 🔜 Nächstes

### 1. Einheitlicher Ausführungspfad

**Ziel:** Jeder Command läuft über einen Host. Keine Ausnahmen.

**Massnahmen:**
- `executor:`-Feld aus yak.yml entfernen (nur noch `host:`)
- `host:` wird Pflichtfeld — Command ohne `host:` ist nicht ausführbar
- Alle eingebauten Commands (`ls`, `cd`, `man`, …) auf `host: /boot/python/runtime` umstellen
- Prüfen: Kann `tree.py` `executor`-Referenzen vollständig entfernen?

**Offene Frage:** Sollen Hosts selbst auch `host:` haben oder `executor: runtime` behalten?
- Variante A: RuntimeExecutor bleibt einziger Sonderfall (Boot-Mechanismus)
- Variante B: Alles ist `host:`, auch Hosts (rekursive Kette)

### 2. `node.entrypoint` statt `_yak/run/app.py` im Host

**Ziel:** Der Tree sagt dem Host, welche Datei zu laden ist — der Host muss `_yak/run/app.py` nicht kennen.

**Massnahmen:**
- `Node` bekommt `entrypoint: Path | None` — gesetzt vom Tree
- `_find_command()` entfällt — Host lädt `node.entrypoint`
- `_shared.py` wird noch generischer

### 3. `_resolve_tree_path()` in den Tree verschieben

**Ziel:** Der Host ruft `tree.resolve(ctx.path, target)` auf, statt selbst Pfade zu berechnen.

**Massnahmen:**
- Tree bekommt Methode `resolve_relative(current: str, target: str) -> str`
- Host importiert diese statt eigener `_resolve_tree_path()`

### 4. UUID-Modulnamen (erledigt)

`mod_name = f"hosted.{uuid.uuid4().hex}"` — verhindert Konflikte bei parallelen Aufrufen.

### 5. Host-Policies

**Ziel:** Hosts definieren die Laufzeitumgebung — nicht nur Sprache, sondern auch Einschränkungen.

**Ideen:**
- `/boot/python/runtime` — normale SDK, Coroutine, Scheduler
- `/boot/python/thread` — blockierende Bibliotheken, run_in_executor
- `/boot/python/process` — isolierter Subprozess
- `/boot/python/sandbox` — eingeschränkte SDK, ReadOnly FS, kein Netzwerk
- `/boot/python/debug` — Tracing, Memory-Profiling, Logging

**Prinzip:** Der Command bleibt identisch — nur der Host-Pfad in yak.yml ändert sich.

### 6. Host-Features (später)

Möglichkeiten, die der Host transparent bieten kann:
- **Progress** — `context.progress(50)` als SDK-API, Host mapped auf Outcome
- **Timeout** — Host bricht nach N Sekunden ab
- **Cancellation** — Ctrl+C → Host → SDK.cancel() → Command
- **Profiling** — Host zeichnet CPU/Memory/I/O auf
- **Tracing** — Host loggt Port-Aufrufe, Laufzeit, Fehler
- **Dependency Injection** — Host injectiert zusätzliche Services in die SDK

### 7. RuntimeExecutor als Boot-Mechanismus

**Ziel:** RuntimeExecutor wird nur noch zum Booten von Hosts verwendet — nicht mehr für User-Commands.

**Massnahmen:**
- Kein Command hat mehr `executor: runtime`
- RuntimeExecutor lädt nur noch Host-Nodes (`/boot/*`)
- Kann `ExecutorRegistry` dann entfallen?

### 8. Yak-Package-Regel: `ls` zeigt nur Yak-Objekte innerhalb eines Packages

**Problem:** `ls /boot/python/` zeigt `runtime/`, `thread/`, `process/`, `_shared.py`, `__pycache__/` — aber `_shared.py` und `__pycache__/` sind Implementierungsdetails.

**Lösung:**
Ein Verzeichnis mit `_yak/` ist ein **Yak-Package**. Innerhalb eines Yak-Packages gehören alle Dateien und Verzeichnisse ohne eigenes `_yak/` zur **privaten Implementierung** und werden von `ls`/`cd` nicht angezeigt.

**Regel:**
> Innerhalb eines `_yak/`-Verzeichnisses wird nichts gezeigt, was nicht selbst ein `_yak/` besitzt.

**Beispiel `/boot/python/`:**
```
Gezeigt:           runtime/ (hat _yak)
                   thread/  (hat _yak)
                   process/ (hat _yak)

Nicht gezeigt:     _shared.py   (kein _yak)
                   __pycache__/ (kein _yak)
                   _yak/ selbst  (Implementierungsgrenze)
```

**Konsequenzen:**
- `_shared.py` braucht keinen Hack — es ist ein privates Implementierungsdetail des Packages
- Die `sys.path.insert()`-Lösung entfällt sobald Hosts per Tree-Resolve auf Package-Interna zugreifen
- Sprachübergreifend: Ruby `lib.rb`, Go `internal/`, C# `Shared/`, Python `_shared.py` — alles private Details

**Umzusetzen in:**
- `tree.py` — Tree-Sicht muss zwischen Yak-Objekten und Nicht-Yak-Objekten unterscheiden
- `ls`/`cd` — Navigationslogik muss private Details ausblenden
- `resolver.py` — Node-Resolution darf nur auf Yak-Objekte zeigen

**Status:** Konzept steht, Umsetzung offen.

## Offene Architekturfragen

1. Dürfen Hosts selbst `host:` haben (rekursive Kette)?
2. Soll `executor:` komplett aus yak.yml verschwinden?
3. Braucht es eine Migration für bestehende Commands?

## Historie

- 16.07. — `/boot/python-host` Spike beweist: Host ist Runtime-Command
- 16.07. — Tree-basierte Host-Delegation (`_make_host_handler`)
- 16.07. — `host: /boot/python/runtime` (voller Pfad) statt Short-Name
- 16.07. — Python-Hosts aufgefächert: `runtime/thread/process/` + `_shared.py`
