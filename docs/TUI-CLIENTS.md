# TUI-Clients für Yakoon

## prompt_toolkit, Textual und die Client-Architektur

---

## 1. Die Client-Architektur von Yakoon

Yakoon ist **client-agnostisch**. Solange ein Client `ProjectionEvent`s empfangen und `InputEvent`s senden kann, ist jedes Framework und jede Plattform möglich.

```
Server (Projection-Streaming)
  │
  ├── WebSocket ──► y5ncli-web (vanilla JS)    → Browser
  │
  └── LocalTransport ──► y5ncli-console (prompt_toolkit) → Terminal
```

Beide Clients konsumieren **dasselbe Protokoll**:
- **Rein:** `ProjectionEvent` mit strukturierten Blöcken (Paragraph, KvBlock, FieldsBlock, ActionBlock, ...)
- **Raus:** `InputEvent` mit Kommando + Token + Payload

Das bedeutet: **Der Server muss nicht geändert werden, um einen neuen Client zu unterstützen.**

---

## 2. Aktueller Client: prompt_toolkit

Der bestehende Konsolen-Client (`y5ncli-console`) verwendet prompt_toolkit.

### Vorteile

- **Leichtgewichtig** – minimale Abhängigkeiten
- **Bewährt** – prompt_toolkit ist stabil und erprobt
- **Einfach** – der Client ist überschaubar (~45 Dateien)
- **Funktioniert** – Terminal-Eingabe und Projection-Ausgabe sind implementiert

### Nachteile

- **Widgets müssen selbst gezeichnet werden** – prompt_toolkit ist ein Baukasten, kein Framework
- **Kein CSS-Styling** – Layout und Design werden in Code definiert
- **Kein Maus-Support** – alles tastaturbasiert
- **Wenig Abstraktion** – du baust dir Struktur (Listen, Tables, Buttons) selbst
- **Aufwändig für reichhaltige UIs** – ein KvBlock oder FieldsBlock braucht viel eigenen Code

---

## 3. Alternative: Textual

[Textual](https://github.com/Textualize/textual) (vom gleichen Team wie Rich) ist ein modernes Python-TUI-Framework mit CSS-Styling, Widgets und Live-Reload.

### Vorteile gegenüber prompt_toolkit

| Feature | prompt_toolkit | Textual |
|---------|---------------|---------|
| **Widgets** | Keine (du zeichnest selbst) | Rich: Button, Tree, Table, Input, Select, ListView, DataTable, Header, Footer, ... |
| **Styling** | Code | CSS-Dateien (`.tcss`) |
| **Layout** | Manuell | Grid, Horizontal, Vertical, Dock, Scroll |
| **Async** | Möglich | First-Class (`async def on_button_clicked`) |
| **Maus** | Begrenzt | Voll |
| **Screencast** | Nein | Eingebaut (`F12` für Replay) |
| **Dev-Tools** | Keine | `textual console`, `textual css`, `textual run --dev` |
| **Live-Reload** | Nein | Ja (CSS-Änderungen sofort sichtbar) |

### Wie ein Textual-Client aussehen könnte

```python
class YakoonTextualClient(App):
    """Yakoon-Client mit Textual."""

    CSS_PATH = "yakoon.tcss"

    def compose(self):
        yield Header(show_clock=True)
        yield YakoonView(id="projection")  # Projection-Ansicht
        yield Input(placeholder="Command...", id="cmd")
        yield Footer()

    async def handle_projection(self, event: ProjectionEvent):
        """Projection in Textual-Widgets mappen."""
        view = self.query_one("#projection")
        await view.clear()

        for block in event.blocks:
            if isinstance(block, HeadingBlock):
                await view.mount(Static(f"[bold]{block.text}[/]", classes="heading"))

            elif isinstance(block, KvBlock):
                table = DataTable()
                table.add_columns("Key", "Value")
                for item in block.items:
                    table.add_row(item.key, item.value)
                await view.mount(table)

            elif isinstance(block, FieldsBlock):
                for field in block.fields:
                    await view.mount(Input(
                        placeholder=field.hint,
                        name=field.name,
                        classes="field",
                    ))

            elif isinstance(block, ActionBlock):
                for action in block.actions:
                    await view.mount(Button(
                        action.label,
                        id=action.command,
                        classes="action",
                    ))
```

### Block-zu-Widget-Mapping

| Block-Typ | Textual-Widget |
|-----------|---------------|
| HeadingBlock | `Static` mit `[bold]` / `[h1]` |
| ParagraphBlock / TextBlock | `Static` |
| ListBlock | `ListView` / `Markdown` |
| KvBlock | `DataTable` |
| FieldsBlock | `Input`-Widgets |
| ActionBlock | `Button`-Widgets |
| RuleBlock | `HorizontalLine` |
| SpacerBlock | `Vertical` mit `height` |
| StackBlock / SectionBlock | `Vertical`-Container |
| FlowBlock | `Horizontal`-Container |
| ImageBlock | `Static` mit Platzhalter |
| InlineStrong | `[bold]` |
| InlineEm | `[italic]` |
| InlineCode | `[monospace]` |
| InlineCmd | `[bold][green]` (klickbar) |
| InlineLink | `[link=...]` |

### CSS-Styling (separat)

```css
/* yakoon.tcss */
Screen {
    background: $surface;
}

#projection {
    height: 1fr;
    overflow-y: scroll;
    border: solid $primary;
    padding: 1;
}

DataTable {
    margin: 1 0;
}

Button {
    margin: 0 1;
}

.field {
    margin: 0 0 1 0;
}

.heading {
    text-style: bold;
    color: $primary;
}
```

---

## 4. Beide Clients sind wartbar

Weil das Protokoll gleich bleibt, können beide Clients parallel existieren:

```
Server (Projection-Streaming)
  │
  ├── WebSocket ──► y5ncli-web (vanilla JS)           → Browser
  │
  ├── LocalTransport ──► y5ncli-console (prompt_toolkit) → Terminal
  │
  └── LocalTransport ──► y5ncli-textual (Textual)     → Terminal (reichhaltig)
```

Der `y5ncli-console` bleibt der leichte, minimalistische Client. Der `y5ncli-textual` kann der reichhaltige Desktop-Client werden.

---

## 5. Zusammenfassung

| Kriterium | prompt_toolkit | Textual |
|-----------|---------------|---------|
| **Abhängigkeiten** | Leicht (~5 Deps) | Mittel (~10 Deps) |
| **Widgets** | Selbst gebaut | Fertig (Rich) |
| **Styling** | Code | CSS |
| **Maus** | Begrenzt | Voll |
| **Dev-Tools** | Keine | Console, CSS, Live-Reload |
| **Lernkurve** | Mittel | Niedrig (CSS!) |
| **Wartbarkeit** | Mehr Code | Weniger Code |

**Fazit:** Ein Textual-Client wäre kein Ersatz für den prompt_toolkit-Client – er wäre eine Ergänzung. Der prompt_toolkit-Client bleibt der Minimal-Client (embedded, SSH, schnelle Tests). Der Textual-Client wird der reichhaltige Desktop-Client (Maus, Tabellen, Buttons, CSS).
