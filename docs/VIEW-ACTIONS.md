# View Actions

Problem: `clear` (und zukünftige Viewport-Operationen wie scroll-to-top,
freeze, layout-umschaltung) operieren nicht auf einzelne Projektionsgruppen,
sondern auf dem gesamten Viewport.

Bisher ist jeder Effekt an eine Projektionsgruppe (`job_id`) gebunden.
`clear` müsste alle Gruppen entfernen.

---

## Anforderung

Ein Flow soll Viewport-Operationen auslösen können:

```python
yield view(action="clear")

# oder später:
yield view(action="scroll_to", target="top")
yield view(action="freeze")
```

Die Operation erreicht den Client, der sie ausführt.

---

## Zwei Ansätze

### A — Neuer `ViewEffect`

**Wirkungskette:**

```
yield view(action="clear")
    │  Outcome(effects=[ViewEffect(action="clear")])
    ▼
Engine._apply_effects()
    │  self.on_view_action(action="clear", session=session)
    ▼
Session._runtime.io.view_action("clear")
    │  BusOutput → SessionBus.broadcast_view_action(…)
    ▼
Client.emit(ViewAction(action="clear"))
    │
    ▼
TextualApp._on_view(event)
    │  isinstance(event, ViewAction) → output.clear()
    ▼
TextualOutput: alle Gruppen entfernen
```

**Neue Elemente:**

| Was | Datei |
|-----|-------|
| `ViewEffect(action, params)` | `base/flow/primitives/effect.py` |
| `view(action, **params)` | `base/flow/dsl.py` |
| `OnViewAction`-Callback | `runtime/machine/engine.py` |
| `IO.view_action()` | `runtime/runtime/bus/bus_output.py` |
| `SessionBus.broadcast_view_action()` | `runtime/runtime/bus/session_bus.py` |
| `ViewAction`-Dataclass | (neu, z.B. `runtime/runtime/bus/view_action.py`) |
| `TextualOutput.clear()` | `apps/textual/output.py` |
| Typ-Check in `_on_view` | `apps/textual/app.py` |

**Berührt:** ~12 Dateien, ~60 LOC

**Vorteile:**
- Klare Trennung: Projection = Content, ViewAction = Viewport
- `view()` ist eigenständig, kein Overload von `out()`
- Neue Viewport-Operationen brauchen nur neuen `action`-String

**Nachteile:**
- Neuer Transport-Pfad neben ProjectionEvent
- `IO`, `BusOutput`, `SessionBus` und `ClientConnection` bekommen neue Methoden
- `Session.emit()` (mit `assert type(event) is ProjectionEvent`) kann nicht
  reused werden — eigener Pfad nötig

---

### B — `view_params` im ProjectionEvent

**Idee:** Kein neuer Effekt, kein neuer Transport. `out()` und `out_text()`
bekamen einen `**view_params`-Parameter, der als Metadatum durch die
bestehende ProjectionEvent-Pipeline läuft.

**Wirkungskette:**

```python
yield out_text("", clear=True)
    │  Outcome(effects=[EmitView(projection, view_params={"clear": True})])
    ▼
Engine._apply_effects()
    │  on_projection(…, view_params={"clear": True})
    ▼
EventStreamOutput.send_projection(…, view_params={"clear": True})
    │
    ▼
Dispatcher → ProjectionEvent(view_params={"clear": True}) → session.emit(…)
    │
    ▼
Client.emit(ProjectionEvent(view_params={"clear": True}))
    │
    ▼
TextualApp._on_view(event)
    │  event.view_params.get("clear") → output.clear()
    ▼
TextualOutput: alle Gruppen entfernen + ggf. projection rendern
```

**Änderungen:**

| Was | Betrifft |
|-----|----------|
| `view_params`-Feld | `EmitView`-Effect, `OnProjection`-Callback, `EventStreamOutput`, `Dispatcher`, `ProjectionEvent` |
| `out(projection, **view_params)` | `dsl.py` — neuer Parameter |
| `out_text(text, **view_params)` | `dsl.py` — neuer Parameter, forwarded an `out()` |
| Client wertet `event.view_params` aus | `apps/textual/app.py` + `output.py` |

Nichts an:

- `IO` / `BusOutput` / `SessionBus` / `ClientConnection`
- Kein neuer Effekt-Type
- Kein neuer Callback in der Engine
- Kein neuer Transport-Pfad

**Vorteile:**
- Minimaler Footprint (~5 Dateien, ~30 LOC)
- Vollständig reibungslos in bestehende Pipeline integriert
- `out()` und `out_text()` sind ohnehin die zentralen Ausgabe-Funktionen
- Später kombinierbar: `out_text("geladen", clear=True)` — erst clear,
  dann neuen Content anzeigen (Client-Entscheidung)
- `view_params` als generischer Container: `{"scroll_to": "top"}`,
  `{"freeze": True}`, `{"layout": "compact"}`, etc.

**Nachteile:**
- Vermischt Content-Projektion und Viewport-Operation in einem Event
- `clear=True` bei `out_text("hallo", clear=True)` ist semantisch ein
  Side-Effekt innerhalb eines Content-Events
- Client muss entscheiden: erst clear, dann rendern? Oder clear ohne
  rendern? (Kann pro Action definiert werden)
- Bei `yield out_text("", clear=True)` läuft eine leere Projection
  durch die Pipeline (begin/emit/finish) — unnötiger Durchlauf

---

## Vergleich

| Kriterium | A (ViewEffect) | B (view_params) |
|-----------|----------------|-----------------|
| Neue Konzepte | ViewEffect, ViewAction, view() | `view_params`-Dict |
| Berührte Dateien | ~12 | ~5 |
| LOC | ~60 | ~30 |
| Projection-Lebenszyklus | Keiner (reiner Befehl) | Läuft trotzdem durch |
| Erweiterbarkeit | Neuer String + ggf. Client-Logik | Neuer Key + Client-Logik |
| Semantik | "Tu was auf dem Viewport" | "Zeige Content + mach nebenbei was" |
| Reinheit | Hoch — getrennte Concerns | Mittel — gemischt |
| Aufwand | Mittel | Gering |
