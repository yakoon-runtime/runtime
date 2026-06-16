# ADH - Architecture Decision Highlight: 
## Job Tree / Subprozesse

> **Status:** Entwurf
> **Datum:** 2026-06-06
> **Prämisse:** Die Runtime hat bereits Flows mit job_id, suspend/resume und Projection-Stream pro Job. Was fehlt, ist die explizite Eltern-Kind-Struktur.

---

## 1. Problem

Die Runtime kann heute genau **einen** Job pro Flow ausführen. Ein Command yieldet Steps, wird suspendiert (await_input) und fortgesetzt – das ist alles linear.

Was nicht geht:

- Ein Job startet einen **Kind-Job** und wartet auf dessen Ergebnis
- Mehrere Jobs laufen **parallel** als Subprozesse eines Eltern-Jobs
- Der Client sieht eine **verschachtelte Projektion** (Job Tree)
- Ein Prozess (z. B. `create_invoice`) ist als **wiederverwendbarer Subprozess** definiert

**Beispiel:** Ein `deploy`-Command soll nacheinander `build`, `test`, `push` ausführen – jeder Schritt ein eigener Job mit eigener Projection.

Aktuell müsste das manuell in einem einzelnen Flow verdrahtet werden. Das skaliert nicht.

---

## 2. Entscheidung

Wir führen drei neue Konzepte ein:

### 2.1 `Process` als first-class Node

Das Patch-Protokoll erhält einen neuen Node-Typ `process`:

```
Node(type="process", id="inv-1", props={
    "name": "create_invoice",
    "status": "running" | "completed" | "failed",
    "job_id": "...",
    "children": [...]
})
```

Die Projection eines Job-Trees ist ein Baum aus `process`-Nodes, die der Client als verschachtelte Gruppen rendert.

### 2.2 Spawn / Join im Protocol

Zwei neue `InputEvent`-Varianten:

```
SpawnProcess(
    job_id=str,           # neue Kind-Job-ID
    process=str,          # Prozess-Name (z.B. "create_invoice")
    kwargs=dict,          # Parameter
    mode="foreground" | "background"  # blockierend oder parallel
)

JoinProcess(
    job_id=str            # auf welchen Kind-Job warten
)
```

- `SpawnProcess` erzeugt einen neuen Flow mit eigener job_id und eigener Projection-Session
- Der Parent wird **suspendiert** (bei mode=foreground) oder **läuft weiter** (mode=background)
- `JoinProcess` suspendiert den Parent, bis der Kind-Job abgeschlossen ist

### 2.3 ProcessRegistry

Prozess-Definitionen werden zentral registriert:

```
registry.register("create_invoice", CreateInvoiceProcess)
registry.register("send_mail", SendMailProcess)
...
```

Ein Process ist ein Generator (wie ein Command), der `yield` für Steps, Spawn und Join verwendet.

```python
def create_invoice(session, customer: str):
    items = yield form.ask("select items ...")
    pdf = yield spawn("generate_pdf", items=items, mode="foreground")
    yield spawn("send_mail", attachment=pdf, mode="background")
    yield show("Invoice created")
```

---

## 3. Konsequenzen

### 3.1 Job Tree in der Projection

Jeder Job projiziert in seinen eigenen Scope. Der Client erhält die Struktur als Baum:

```
deploy (job=abc)
 ├ build (job=def)      → completed
 ├ test (job=ghi)        → completed
 └ push (job=jkl)        → running
```

Die Textual-Output-Komponente rendert `process`-Nodes als eingerückte Gruppen mit Status-Indikator.

### 3.2 Agent = Job, der Spawn darf

Die Definition aus dem Gespräch:

> Agent = Job, der andere Jobs starten darf.

Das ist keine LLM-Entscheidung, sondern eine Runtime-Entscheidung. Ein Agent ist ein Process, der `spawn()` verwendet. Die Entscheidungslogik kann Python, BPMN, Regelwerk oder später LLM sein.

### 3.3 Suspension und Auflösung

Ein `spawn` im foreground-Mode suspendiert den Parent, sobald der Kind-Job startet. Der Parent wird fortgesetzt, wenn der Kind-Job completed/failed ist.

```
Parent: [spawn → suspend] → [join → resume]
Child:  [start → ... → complete]
```

Ein `spawn` im background-Mode startet den Kind-Job sofort, der Parent läuft weiter. Der Kind-Job projiziert eigenständig.

### 3.4 Keine Änderung am Scheduler

Der Scheduler dispatcht weiterhin nach job_id. `spawn` erzeugt einfach einen neuen Flow mit neuer job_id. Der `join` blockiert den Parent-Flow (suspend), bis die Kind-job_id completed ist. Das ist bereits vorhandene Mechanik (`await_input` / `resume`).

---

## 4. Alternativen

### 4.1 Alles im selben Flow

Ein einziger Flow bildet den gesamten Prozess ab. Problem: Keine parallelen Jobs, keine getrennten Projectionen, keine Wiederverwendung von Subprozessen.

### 4.2 Manuelle Job-ID-Vergabe

Der Command-Erzeuger vergibt job_ids für Sub-Jobs selbst. Problem: Keine Runtime-Garantie für Lifecycle, keine Baumstruktur in der Projection, kein `join`.

### 4.3 Externer Workflow-Engine (Temporal, Prefect)

Würde eine zweite Runtime neben der bestehenden bedeuten. Verletzt das Architekturprinzip: "Die Runtime ist der einzige Akteur."

---

## 5. Fahrplan

1. **ProcessRegistry** – Prozesse als Generator-Funktionen registrieren
2. **SpawnProcess / JoinProcess** – InputEvent-Varianten im Protocol
3. **Spawn/Join-Handling im Runner** – neuen Flow starten / auf job_id warten
4. **Process-Node in der Projection** – Baumstruktur im Patch-Protokoll
5. **Client-Rendering** – Verschachtelte Gruppen in TextualOutput
6. **Background-Mode** – Nicht-blockierendes Spawn
7. **Persistence** – Job-Tree speichern und restore

---

## 6. Offene Fragen

- Soll `spawn` ein `yield` sein (blockierend) oder ein `await`-ähnlicher Aufruf?
- Wie tief darf der Job-Tree werden? (aktuell kein Limit)
- Was passiert mit Kind-Jobs, wenn der Parent failed? (Cascade-Cancel)
- Soll es einen `cancel(job_id)`-Befehl geben?
