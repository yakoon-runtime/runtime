# Das Yakoon-Projection-System

## Konzept, Pipeline und Protokoll

---

## 1. Was ist eine Projection? (Konzept)

Eine **Projection** ist das kanonische, strukturierte UI-Dokument im Yakoon-System. Sie ist die serverseitige Repräsentation dessen, was ein Benutzer sieht – eine vollständig aufgelöste, strukturierte Ansicht, die aus einem **Template + Zustand** in eine transportierbare Form **projiziert** wird.

Der Begriff "Projection" ist bewusst gewählt:

- **Nicht "View"** – eine View impliziert eine aktive Rendering-Komponente. Die Projection ist ein **Dokument**, kein aktives Objekt.
- **Nicht "Template"** – ein Template ist die Vorlage. Die Projection ist das **fertig gerenderte Ergebnis**.
- **Projektion** – im mathematischen Sinne: eine deterministische Abbildung von Zustand auf Darstellung. `projection = f(state)`.

Die Projection ist die Brücke zwischen:

- **Intention** (was das System dem Benutzer sagen will)
- **Struktur** (wie diese Intention als Dokument organisiert ist)
- **Transport** (wie das Dokument inkrementell zum Client geliefert wird)

```python
@dataclass(frozen=True)
class Projection:
    id: str                    # z.B. "prj.a1b2c3..."
    kind: str = "projection"
    header: ProjectionHeader | None  # Dokument-Metadaten
    blocks: list[Block]              # Der Dokument-Body
```

---

## 2. Architektur-Prinzip

> **Flow bestimmt State. State bestimmt Projection. Projection bestimmt UI.**

Die Projection ist eine **deterministische Funktion des Zustands**. Gleicher Zustand → gleiche Projection. Das erlaubt:

- **Idempotenz**: Wiederholtes Projizieren des gleichen Zustands erzeugt das gleiche Dokument
- **Testbarkeit**: Projectionen können ohne Runtime getestet werden (reine Funktion)
- **Caching**: Projectionen können gecached werden, solange der Zustand gleich bleibt
- **Zeitreisen**: Historische Zustände können jederzeit neu projiziert werden

Die Projection selbst ist **immutable** (frozen dataclass) – einmal erzeugt, ändert sie sich nicht. Änderungen werden durch eine **neue Projection** mit neuer ID abgebildet.

---

## 3. Die Pipeline im Überblick

```
Template (.sam)        Rendered XML            Projection             Client Events
    │                       │                       │                       │
    ▼                    Jinja2                     ▼                    Event
  state dict ──►  RenderEngine ──► Compiler ──► Dispatcher ──► WebSocket
                      │               │               │
                  autoescape=False   4 Stufen:    batching,
                  StrictUndefined    tokenize →   flush,
                  finalize-hook      AST →        patch ops
                                     normalize →
                                     build
```

### Schritt 1: Rendern (Jinja2 → String)

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/projection/rendering/engine.py`

Ein `.sam`-Template wird mit einem `state`-Dictionary durch Jinja2 gerendert. Das Ergebnis ist ein **XML-artiger String** (kein HTML!).

```python
class JinjaRenderEngine:
    def __init__(self):
        self.env = Environment(
            loader=...,              # Lädt .sam-Dateien aus Ressourcen
            undefined=StrictUndefined,  # Zugriff auf undef. Variable = Fehler
            autoescape=False,          # Würde XML-Tags zerstören
            finalize=finalize_template_value,  # blockt Nicht-Skalare
        )

    def render_str(self, name: str, context: dict) -> str:
        return self.env.get_template(name).render(**context)
```

**Sicherheitsmassnahmen:**
- `StrictUndefined` – Zugriff auf nicht existierende Variablen wirft einen Fehler (kein stilles `None`)
- `finalize_template_value` – verhindert, dass Nicht-Skalar-Objekte (Objekte, Listen, Dicts) ins gerenderte Template durchsickern
- `autoescape=False` ist bewusst – das Template-DSL erzeugt strukturiertes XML, kein HTML. Escaping würde die Tag-Syntax zerstören. Output, der Benutzerdaten enthält, muss vorher im State bereinigt werden.

### Schritt 2: Kompilieren (String → Projection)

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/projection/compiler/compiler.py`

Der Compiler läuft in **4 Phasen**:

#### Phase 1: Tokenize

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/projection/compiler/tokens.py`

Ein Regex-basierter XML-Tokenizer wandelt den gerenderten String in eine flache Liste von Token:

```python
@dataclass
class Token:
    type: Literal["TEXT", "OPEN", "CLOSE", "SELF"]
    tag: str | None
    attrs: dict | None
    content: str | None
```
- Entfernt HTML-Kommentare (`<!-- ... -->`)
- Findet Tags via `<(/?)(\w+)([^>]*)>` und parst Attribute via `(\w+)="([^"]*)"`
- Text zwischen Tags wird als `TEXT`-Token emittiert
- Self-closing-Tags (`<br/>`) werden als `SELF` erkannt

#### Phase 2: Build AST

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/projection/compiler/ast.py`

Baut einen Baum aus der flachen Token-Liste mittels eines Stacks:

```python
class Node: pass                         # abstrakt
class TextNode(Node, text: str)          # Blatt
class ElementNode(Node, tag, attrs, children):  # Ast-Knoten
```

- `TEXT` → `TextNode` an aktuelles Stack-Top
- `OPEN` → neues `ElementNode`, auf Stack
- `SELF` → `ElementNode` ohne Kinder (kein Stack-Push)
- `CLOSE` → Stack-Pop mit Tag-Validierung

#### Phase 3: Normalize

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/projection/compiler/normalize.py`

Mutiert den AST in-place:
- Kollabiert Whitespace: `re.sub(r"\s+", " ", text)` + `.strip()`
- Ausnahme: `<code>` und `<pre>` behalten Whitespace
- Rekursiver Baumdurchlauf

#### Phase 4: Build (Map → Projection)

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/projection/compiler/mapper/core.py`

Der `Mapper` transformiert den normalisierten AST in ein `Projection`-Objekt:

1. **`map_projection(root)`**: Erzeugt Projection-ID (`"prj." + uuid.hex`), mapped `<header>` zu `ProjectionHeader`, mapped Kind-Knoten zu `Block[]`, vergibt hierarchische IDs
2. **`_map_nodes(nodes)`**: Puffert aufeinanderfolgende Text/Inline-Knoten, mapped Block-Tags via registrierte `BlockMapper`
3. **Block-Mapper**: Jeder Tag hat einen eigenen Mapper (paragraph, heading, list, kv, section, etc.)
4. **Inline-Mapper**: Für Inline-Tags (strong, em, code, link, cmd, etc.) innerhalb von Text

### Schritt 3: Dispatchen (Projection → Client-Events)

**Datei:** `runtime/y5ncore-runtime/src/y5n/runtime/projection/transport/dispatcher.py`

Der `EventDispatcher` wandelt eine Projection in eine Sequenz von `ProjectionEvent`-Nachrichten um:

```python
class ProjectionEvent:
    kind: "view_event"
    id: str                    # Projection-ID
    header: ProjectionHeader
    ctx: InputContext
    state: ProjectionState
    job_id: str
    patch: Patch               # Inkrementelle Änderungen
```

**Patch-Operationen:**

| Op | Zweck |
|----|-------|
| `PatchReset` | Gesamte Client-Ansicht leeren |
| `PatchAppendStructure` | Node(s) zum Baum hinzufügen |
| `PatchFinishNode` | Node als "fertig gerendert" markieren |

**Batching:**
- `BATCH_SIZE = 128` Ops – flush bei voller Queue
- `MAX_BUFFER_DELAY = 0.05s` – zeitgesteuerter Flush
- Abhängigkeitsfilter: `PatchAppendStructure` wird nur gesendet, wenn der Eltern-Node bereits veröffentlicht wurde

### Schritt 4: Serialisieren (JSON für den Draht)

**Datei:** `runtime/y5ncore-base/src/y5n/base/projection/wire/serialize.py`

```python
def serialize_event(event: ProjectionEvent) -> dict:
    # → JSON-kompatibles Dict
```

- Inline-Objekte werden in `{type: "...", ...}`-Format konvertiert
- Strukturelle Felder (`block`, `blocks`, `items`) werden aus Props ausgeschlossen
- Primitive passieren direkt; komplexe Objekte fallen zurück auf `str()`

---

## 4. Das Block-/Inline-Modell

### Block-Typen (Dokumentstruktur)

**Datei:** `runtime/y5ncore-base/src/y5n/base/projection/model/block.py`

| Block | Tag | Zweck |
|-------|-----|-------|
| **ParagraphBlock** | `<p>`, `<text>` | Textabsatz |
| **HeadingBlock** | `<h1>..<h3>` | Überschrift (level 1-3) |
| **ListBlock** | `<list>` | Geordnete/un-geordnete Liste |
| **ListItemBlock** | `<item>` | Ein Listeneintrag |
| **KvBlock** | `<kv>` | Schlüssel-Wert-Tabelle |
| **KvItemBlock** | `<item>` | Ein Schlüssel-Wert-Paar |
| **SectionBlock** | `<section>` | Gruppierungs-Container |
| **StackBlock** | `<stack>` | Vertikaler Stapel-Container |
| **FlowBlock** | `<flow>` | Flow-Layout-Container |
| **RuleBlock** | `<rule/>` | Horizontale Linie |
| **SpacerBlock** | `<spacer/>` | Vertikaler Abstand |
| **FieldsBlock** | `<fields>` | Interaktive Formularfelder |
| **ActionBlock** | `<actions>` | Aktions-Buttons |
| **ImageBlock** | `<image/>` | Bild-Referenz |
| **TextBlock** | (implizit) | Freitext mit Inline-Markup |

**Container-Blöcke** (Section, Stack, Flow) enthalten rekursiv weitere Blöcke.

### Inline-Typen (innerhalb von Text)

**Datei:** `runtime/y5ncore-base/src/y5n/base/projection/model/inline.py`

| Inline | Tag | Zweck |
|--------|-----|-------|
| **InlineText** | (roher Text) | Klartext |
| **InlineStrong** | `<strong>` | Fett |
| **InlineEm** | `<em>` | Kursiv |
| **InlineUnderline** | `<u>` | Unterstrichen |
| **InlineCode** | `<code>` | Monospace/Code |
| **InlineLink** | `<link href="...">` | Hyperlink |
| **InlineCmd** | `<cmd command="...">` | Ausführbarer Befehl |
| **InlineArg** | `<arg>` | Argument/Parameter |
| **InlineSelect** | `<select value="...">` | Auswählbarer Wert |
| **InlineMark** | `<mark type="...">` | Semantische Hervorhebung |
| **InlineSpace** | `<space count="..."/>` | Horizontaler Abstand |
| **InlineBreak** | `<br count="..."/>` | Zeilenumbruch |

### Felder (Interaktive Formulare)

**Datei:** `runtime/y5ncore-base/src/y5n/base/projection/model/field.py`

```python
@dataclass
class Field:
    policy: str        # z.B. "system:string"
    name: str
    title: str
    required: bool
    hint: str | None
    default: str | None
    type: FieldType    # INT, BOOL, DATE, TIME, FLOAT, STRING, DATETIME
    lookup: str | None # Referenz auf eine Lookup-Projection
    options: list | None
    # Runtime-State:
    value: str | None
    query: str | None
    errors: list[str]
```

### Actions (Buttons)

**Datei:** `runtime/y5ncore-base/src/y5n/base/projection/model/action.py`

```python
@dataclass
class Action:
    label: str         # Anzeigetext
    command: str       # Auszuführender Befehl
    scope: str | None  # Optionaler Scope-Indikator
```

---

## 5. Die Template-Sprache (`.sam`-Dateien)

`.sam`-Dateien sind **Jinja2-Templates**, die ein **XML-artiges DSL** produzieren.

### Beispiel: `welcome/result.sam`

```xml
<br/>
WILLKOMMEN
<br count="2"/>
{% if state.name %}
  {{ state.name }}
{% endif %}
Was du jetzt tun kannst:
<rule/>
<list>
  <item>man          - Zeigt Manual fur Befehle</item>
  <item>use prg      - Startet ein Programm</item>
  <item>version      - Zeigt Systeminformationen</item>
</list>
```

### Beispiel: `test/ask1.sam` (mit interaktivem Formular)

```xml
<p>Suche nach <strong>Projekten</strong></p>
<fields name="project">
  <field
    name="project_name"
    policy="system:string"
    title="Projektname"
    lookup="city.show.all"
  />
</fields>
<actions>
  <action command="test save" scope="project">Speichern</action>
</actions>
```

### Jinja2-Integration

- `{{ state.field }}` – Variablen-Interpolation
- `{% if ... %} / {% for ... %}` – Kontrollfluss
- `{%- ... -%}` – Whitespace-Kontrolle
- Eigene Filter (z.B. `|ljust`) für Terminal-Ausrichtung

### Tag-Vollständigkeit

| Tag | mapped zu |
|-----|-----------|
| `<header role="..." title="...">` | `ProjectionHeader` |
| `<p>`, `<text>` | `ParagraphBlock` |
| `<h1>`..`<h3>` | `HeadingBlock(level=n)` |
| `<list><item>` | `ListBlock(ListItemBlock[])` |
| `<kv><item key="...">` | `KvBlock(KvItemBlock[])` |
| `<section>` | `SectionBlock` |
| `<stack>` | `StackBlock` |
| `<flow>` | `FlowBlock` |
| `<rule/>` | `RuleBlock` |
| `<spacer/>` | `SpacerBlock` |
| `<fields><field/>` | `FieldsBlock(Field[])` |
| `<actions><action>` | `ActionBlock(Action[])` |
| `<image/>` | `ImageBlock` |
| `<strong>`, `<em>`, `<u>`, `<code>` | Inline-Formatierung |
| `<link href="...">` | `InlineLink` |
| `<cmd command="...">` | `InlineCmd` |
| `<arg>` | `InlineArg` |
| `<select value="...">` | `InlineSelect` |
| `<mark type="...">` | `InlineMark` |
| `<space/>`, `<br/>` | Abstände |

---

## 6. Streaming (PerceptualStream)

**Datei:** `runtime/y5ncore-base/src/y5n/base/projection/percept/perceptual.py`

Das `PerceptualStream` implementiert ein **zeichenweises Text-Streaming** für Terminal-Output, das menschenähnliche Tippgeschwindigkeit simuliert. Angetrieben von einer Game-Loop-artigen `step(dt)`-Methode.

### Konstanten

| Konstante | Wert | Bedeutung |
|-----------|------|-----------|
| `FRAME_INTERVAL` | 1/15 ≈ 66ms | Zeit zwischen Zeichen-Chunks |
| `FRAME_BUDGET` | 12 | Max Events pro Frame |
| `INITIAL_DELAY` | 0.06s | Verzögerung vor erstem Output |
| `CHARS_START` | 6 | Chunk-Grösse am Anfang (0-15%) |
| `CHARS_MID` | 18 | Chunk-Grösse in der Mitte (15-50%) |
| `CHARS_FAST` | 48 | Chunk-Grösse nach 50% |
| `JITTER` | 0.02s | Zufalls-Jitter pro Frame |

### Algorithmus (`step(dt)`)

1. Wenn pausiert oder schlafend (`_sleep > 0`): Timer dekrementieren, zurück
2. **Bis zu `FRAME_BUDGET` (12) Events pro Frame** verarbeiten
3. Für jedes `TextEvent`:
   - **Chunk-Grösse berechnen** basierend auf Fortschritt (Start/Mitte/Schnell)
   - **Natürliche Tipp-Heuristik**: Wenn Chunk ein langes Wort (>12 Zeichen ohne Leerzeichen), Chunk halbieren
   - **Wort-bewusstes Chunking**: Wenn Chunk nicht mit Whitespace endet, bis zur nächsten Wortgrenze verlängern
   - Chunk via `_on_text(node_id, key, chunk)` emittieren
   - **Pacing anwenden** (`_apply_pacing`)
4. Für jedes `FinishEvent`: `_on_block_finished(node)` aufrufen
5. Wenn alle Events verbraucht: Zustand zurücksetzen, `_on_stream_finished` aufrufen

### Pacing (`_apply_pacing`)

- **Fast-Forward-Modus**: Keine Verzögerung zwischen Chunks
- **Interpunktion-Pausen**: `.!?` → 180ms, `:` → 120ms, `\n` → 80ms, `\n\n` → 300ms
- **Normal-Modus**: `FRAME_INTERVAL + zufälliger Jitter` zwischen Chunks
- **Erster Chunk**: Immer `INITIAL_DELAY` (60ms)

### Frame-Budget

`FRAME_BUDGET = 12` verhindert, dass der Stream zu viele Events pro Frame-Tick verarbeitet – die UI bleibt reaktionsfähig. Wenn eine Interpunktions-Pause auftritt, wird die Verarbeitung mid-Frame ausgesetzt (`should_pause = True`).

### Profiler

`StreamProfiler` trackt:
- Events/s, Chunks/s, Chars/s, Sleep-Ratio
- Für Performance-Debugging des PerceptualStream

---

## 7. Transport-Protokoll

### Transport-Node

Jeder Block wird in einen transportierbaren `Node` umgewandelt:

```python
@dataclass
class Node:
    id: str                  # z.B. "prj.a1b2c3.0.1"
    type: str                # z.B. "text", "list", "kv"
    parent: str | None       # Eltern-Node-ID
    depth: int
    props: dict              # Block-Felder (minus id/type)
```

### Patch-Operationen

| Op | Beschreibung |
|----|-------------|
| `PatchReset` | Client-Ansicht komplett zurücksetzen |
| `PatchAppendStructure` | Einen oder mehrere Nodes zum Baum hinzufügen |
| `PatchFinishNode` | Node als "fertig" markieren (alle Kinder emittiert) |

### Dispatcher-Lebenszyklus

1. **`begin_projection()`** → erzeugt `_ViewStream`, emittiert `ProjectionEvent` mit Header + `PatchReset`
2. **`emit_block()`** → rekursiver Baumdurchlauf: für jeden Block ein `PatchAppendStructure`, dann `PatchFinishNode`
3. **`emit_projection()`** → emittiert alle Blöcke einer Projection
4. **`finish_projection()`** → flush, finales Event, Stream aufräumen
5. **`abort_projection()`** → Queue leeren, Finish emittieren, Stream entfernen

### Serialisierung am Draht

```json
{
  "id": "prj.a1b2c3d4e5...",
  "kind": "view_event",
  "header": {
    "role": "success",
    "title": "Version 0.4.0"
  },
  "patch": {
    "ops": [
      {"reset": {}},
      {"appendStructure": {
        "node": {"id": "prj.a1b2c3d4e5.0", "type": "text", "parent": null,
                 "props": {"text": [{"type": "text", "text": "Version 0.4.0"}]}}
      }},
      {"finishNode": {"id": "prj.a1b2c3d4e5.0"}}
    ],
    "final": true
  }
}
```

---

## 8. Zusammenfassung: Projektion als Architekturkonzept

```
┌─────────────────────────────────────────────────────────────┐
│                    YAKOON PROJECTION SYSTEM                   │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Flow ──besitzt──► State ──wird projiziert──► Projection    │
│                     (dict)         f(state)     (immutable)   │
│                                                              │
│  Projection ──wird dispatched──► ProjectionEvent[]           │
│               (Dispatcher)        (Patch-Operationen)         │
│                                                              │
│  ProjectionEvent ──serialisiert──► JSON ──WebSocket──► Client│
│                                                              │
│  Client ──deserialisiert──► Patch ──applied auf──► DOM-Tree  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

**Kernkonzepte:**

| Konzept | Bedeutung |
|---------|-----------|
| **Projection** | Immutables, strukturiertes UI-Dokument, `f(state)` |
| **Template** | `.sam`-Datei: Jinja2 + XML-DSL |
| **Compiler** | 4-Phasen-Pipeline: Tokenize → AST → Normalize → Build |
| **Block** | Strukturelement (paragraph, list, kv, section, ...) |
| **Inline** | Textelement (strong, code, link, cmd, ...) |
| **Patches** | Inkrementelle Baum-Operationen (Reset, Append, Finish) |
| **PerceptualStream** | Zeichenweises Streaming mit Tipp-Simulation |
| **Dispatcher** | Transformiert Projection in Client-Events mit Batching |
