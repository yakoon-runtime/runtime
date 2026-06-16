# RuntimeInfo — Version an den Client bringen

## Ziel

Der Status-Balken zeigt `yakoon v0.71.0 · space:/$` — die Version
kommt vom Server, nicht aus einem Hardcoded-String im Client.

```python
connection.runtime_info
# → RuntimeInfo(version="0.71.0", build="abc1234")
```

## Heutiger Zustand

| Aspekt | Status |
|--------|--------|
| Brand-String `"yakoon"` | Hardcoded in `app.py:70` |
| Version im Client | Nicht vorhanden |
| Version auflösen | `_get_platform_version()` in `spaces/.../version.py` (git → version.txt → "unknown") |
| Connection-Handshake | Keiner (Client sendet `connect`, Server ignoriert es) |
| Metadaten im Wire-Protokoll | Keine |

## RuntimeInfo-Dataclass

```python
# runtime/y5ncore-base/src/y5n/base/runtime/info.py

@dataclass(frozen=True, slots=True)
class RuntimeInfo:
    version: str          # "0.71.0"
    build: str | None     # "abc1234" (git commit)
```

Aufgelöst wird in `runtime/settings/version.py`:

```python
def resolve_runtime_info() -> RuntimeInfo:
    version = _resolve_version().lstrip("v")
    build = _resolve_build()
    return RuntimeInfo(version=version, build=build)
```

Resolution-Chain: `importlib.metadata` > git tag > version.txt > `"unknown"`

## Datenfluss

```
RuntimeApp/RuntimeHost (kennt info: RuntimeInfo)
 │
 ├── connect(connection)
 │   └── connection.runtime_info = self.info
 │       └── ClientConnection.runtime_info: RuntimeInfo | None
 │
 ├── Session.__init__(runtime_info)
 │   └── self.runtime_info = runtime_info
 │
 └── Session._attach_state(event)
     └── ProjectionState(runtime_version=self.runtime_info.version, ...)
         └── ProjectionEvent → serialisiert → Client
             └── TextualApp._on_view(event)
                 └── self._status_brand.update(f"yakoon v{event.state.runtime_version}")
```

## Drei Ansätze

### A — Version in ProjectionState (empfohlen)

`ProjectionState` bekommt ein Feld `runtime_version: str | None`.
`Session._attach_state()` setzt es aus der RuntimeInfo.
Der Client liest es im `_on_view()`-Handler.

**Aufwand:**

| Schritt | LOC | Datei |
|---------|-----|-------|
| `RuntimeInfo`-Dataclass | 5 | `y5n/base/runtime/info.py` (neu) |
| `resolve_runtime_info()` | 10 | `y5n/base/runtime/info.py` |
| `RuntimeHost.info` + Init | 3 | `machine/host.py` |
| `connection.runtime_info` | 1 | `clients/connection.py` |
| `connect()` setzt info | 1 | `machine/host.py` |
| `Session.runtime_info` + Init | 2 | `sessions/session.py` |
| `ProjectionState.runtime_version` | 1 | `transfer/event.py` |
| `_attach_state()` setzt version | 1 | `sessions/session.py` |
| Client: Brand updaten | 1 | `textual/app.py` |
| **Summe** | **25** | |

**Pro:** Minimaler Footprint, kein neuer Event-Typ, kein neuer Transport-Pfad.

**Contra:** Version erst verfügbar, nachdem das erste ProjectionEvent ausgeliefert wurde.
In der Praxis kein Problem (`space:/$` wird beim ersten Rendering gesetzt).

---

### B — Dediziertes Info-Event beim Handshake

Server schickt nach dem Accept ein Metadata-Event:

```json
{"type": "info", "payload": {"version": "0.71.0", "build": "abc1234"}}
```

Der Client speichert es im Connection-Objekt und zeigt es an.

**Aufwand:** Neuer Event-Typ im Wire-Protokoll, neuer Handler im Client,
neuer Sendepfad im Transport. Geschätzter Aufwand: ~80 LOC.

**Pro:** Version sofort nach connect verfügbar, saubere Trennung.

**Contra:** Deutlich mehr Code, neue Message-Type, neuer Handler auf beiden Seiten.

---

### C — `connection.runtime_info` per IPC

`ClientConnection.runtime_info` ist eine `async`-Property, die per
Request-Response über den Transport abgefragt wird.

**Aufwand:** Request-Response-Infrastruktur, neuer Message-Type, neuer
Handler. Geschätzter Aufwand: ~120 LOC.

**Pro:** Lazy, nur bei Bedarf.

**Contra:** Asynchrone Abfrage nötig, aufwändig.

---

## Empfehlung

**A** — Version in `ProjectionState`. Die Verzögerung bis zum ersten Event
ist irrelevant, weil der Client vorher ohnehin nichts anzeigt.

Implementierungsschritte:
1. `RuntimeInfo`-Dataclass in `y5n/base/runtime/info.py`
2. `resolve_runtime_info()` in `y5n/runtime/settings/version.py` (importlib.metadata > git > version.txt > unknown)
3. `RuntimeHost.info` befüllen (init aus `resolve_runtime_info()`)
4. `ClientConnection.runtime_info`-Attribut
5. `RuntimeHost.connect()` setzt `connection.runtime_info`
6. Textual: Status-Bar rechts mit `v{version}`
