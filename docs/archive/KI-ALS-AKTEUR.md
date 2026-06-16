# KI als Akteur

## Warum Yakoon KI nicht als Sonderfall behandeln muss

---

## 1. Das Problem in klassischen Architekturen

In den meisten Systemen gibt es **zwei völlig verschiedene Interfaces**:

```
Mensch → GUI (Buttons, Formulare, Klicks)
Maschine → API (REST, GraphQL, gRPC)

→ Zwei verschiedene Parser
→ Zwei verschiedene Auth-Mechanismen (Session vs. Token)
→ Zwei verschiedene Output-Formate (HTML vs. JSON)
→ Zwei verschiedene Fehlerbehandlungen
→ Zwei Deployment-Profile (UI-Server + API-Server)
```

Eine KI muss dann beides können oder es gibt eine **dritte Schnittstelle**: einen "AI Agent SDK", der die REST-API wrappt. Das ist dreifacher Aufwand.

---

## 2. Yakoon hat nur ein Interface: Den Node-Baum

In Yakoon gibt es **genau einen Weg, mit dem System zu interagieren**:

```python
# Ein InputEvent. Egal von wem.
@dataclass
class InputEvent:
    data: str            # Das Kommando
    tokens: list[str]    # Die Argumente
    payload: Any         # Optionale Daten
    context: InputContext  # Wer, wo, wann
```

Ob der Input vom Menschen kommt (Tastatur, Sprache) oder von einer Maschine (KI, Script, anderer Service) – **der Parser ist derselbe**:

```
Mensch tippt:   "invoice list --status=open"
KI generiert:   "invoice list --status=open"
Script sendet:  "invoice list --status=open"

→ InputParser.parse() → InputEvent
→ InvocationResolver.resolve() → Node
→ CommandEngine.dispatch() → Flow
```

**Das System unterscheidet nicht zwischen Mensch und Maschine.** Es gibt nur:
- Einen **Akteur** (wer die Session hält)
- Eine **PermissionSet** (was der Akteur darf)
- Einen **Input** (was der Akteur schickt)

---

## 3. Was Yakoon der KI bereits bietet

### 3.1 Selbstbeschreibende Nodes

Jeder Node im Baum trägt seine Beschreibung in sich:

```python
Node(
    key="invoice",
    name="Rechnungen",
    # Manpage als Resource
    invocations=[
        Invocation(args=["list"], options=["status", "from", "to"]),
        Invocation(args=["show"], options=["id"]),
        Invocation(args=["pay"], options=["id", "method"]),
    ],
    children=[...],  # Sub-Kommandos
)
```

Eine KI kann den Node-Baum traversieren und bekommt:
- Welche Kommandos existieren (`find_resolvable()`)
- Welche Argumente und Optionen jedes Kommando erwartet (`invocations`)
- Welche Sub-Kommandos es gibt (`children`)

Das entspricht einem **maschinenlesbaren OpenAPI-Schema** – nur dass es Live ist und nicht generiert werden muss.

### 3.2 Hierarchische Sichtbarkeit

Die KI sieht nur, was der aktuelle Node-Kontext hergibt:

```
/shell (Akteur ist hier)
├── system/
│   ├── ls, cd, man, ...
├── runtime/
│   ├── version, welcome, ...
├── ident/
│   ├── user, group, grant, ...
├── billing/                    # Nur wenn Akteur berechtigt
    ├── invoice/list
    ├── invoice/show
    ├── invoice/pay
```

Die Permission-Checker (`OnAuthorizeRead`, `OnAuthorizeWrite`) werden beim Node-Resolution-Prozess ausgeführt. Die KI bekommt nur das zu sehen, wofür der Session-Inhaber autorisiert ist – **kein separater Auth-Zweig nötig**.

### 3.3 Strukturierte Projections als Antwort

Egal ob Mensch oder KI – die Antwort ist immer eine `Projection`:

```json
{
    "kind": "view_event",
    "header": {"role": "success", "title": "3 Rechnungen offen"},
    "blocks": [
        {"type": "list", "items": [
            {"key": "INV-001", "value": "490,00 €", "status": "offen"},
            {"key": "INV-002", "value": "120,00 €", "status": "offen"}
        ]}
    ]
}
```

Eine KI kann diese strukturierte Antwort **direkt weiterverarbeiten** (kein HTML-Parsing, kein Screen-Scraping). Ein Mensch sieht sie gerendert im Terminal/Web.

**Dasselbe `ProjectionEvent` – zwei Konsumenten, zwei Interpretationen.**

---

## 4. Architekturentscheidung (aus DECISIONS.md)

> **2025-05-29: Umgang mit KI (Intent Mapping)**
>
> Entscheidung: Die KI fungiert ausschließlich als Berater zur
> Bedeutungserschließung von Benutzereingaben (Intent Mapping). Sie wählt
> mögliche Commands und Domains aus – führt aber nichts aus.
>
> Begründung: Die Plattform bleibt alleinige ausführende Instanz (Akteur).
> Die KI ist rein unterstützend (Berater) tätig. Damit wird verhindert, dass
> das Modell außerhalb der gültigen Systemlogik halluziniert.
>
> Leitsatz: **"Wer ist Akteur, wer ist Berater?"**
> Nur die Plattform darf handeln. Die KI darf vorschlagen.

Diese Entscheidung ist wichtig: Die KI ist **nicht autonom**. Sie schlägt ein `InputEvent` vor, aber die Plattform führt es aus – mit Permission-Check, Audit und voller Systemintegrität.

```
Mensch: "Zeig mir alle offenen Rechnungen"
  → KI: intent = "invoice list --status=open"
  → System: PermissionChecker.prüfen()
  → System: CommandEngine.dispatch("invoice list --status=open")
  → System: Flow läuft, Projection wird erzeugt
  → System: Projection an Session gesendet
  → KI (optional): "Es sind 3 Rechnungen offen. Soll ich ...?"
  → Mensch/Ja: "pay INV-001"
```

---

## 5. Was eine KI im System ist

Eine KI ist in Yakoon **nichts Besonderes**:

```
              ┌─────────────────────────────────┐
              │         Session                  │
              │  ┌───────────────────────────┐   │
              │  │     Node Tree             │   │
              │  │  (Commands, Sub-Commands) │   │
              │  └───────────────────────────┘   │
              │         ▲                        │
              │         │ InputEvent              │
              │         │ (data, tokens, ctx)     │
              │         │                        │
              │  ┌──────┴────────┐               │
              │  │   InputRouter │               │
              │  └──────┬────────┘               │
              │         │                        │
              │  ┌──────┴────────┐               │
              │  │     Runner    │               │
              │  └──────────────┘               │
              └─────────────────────────────────┘
                         ▲
          ┌──────────────┼──────────────┐
          │              │              │
     ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
     │Mensch   │   │ KI      │   │ Script  │
     │(Tastatur)│   │(ChatGPT)│   │(Cron)   │
     └─────────┘   └─────────┘   └─────────┘
```

Alle drei sind **Input-Quellen**. Der `Runner` behandelt sie gleich. Der einzige Unterschied ist, wer die Session hält und welche PermissionSet gilt.

---

## 6. Was folgt daraus

### Keine separaten APIs für KI

Weil der Node-Baum das einzige Interface ist, braucht es **keinen separaten AI-API-Endpunkt**. Die KI schreibt in den Session-Input-Kanal. Das System tut das, was es immer tut.

### Keine speziellen Output-Formate

Die `Projection` ist das einzige Output-Format. Die KI erhält dasselbe strukturierte Objekt wie der Client. Sie kann es parsen, zusammenfassen oder direkt weiterverarbeiten.

### Keine spezielle Auth

Permissions gelten für die Session – nicht für "Mensch" vs. "Maschine". Wenn die KI im Namen eines Users handelt, gelten dessen Berechtigungen. Kein API-Key-Management, keine OAuth-Scopes, kein JWT neben der Session.

### Kein Context-Verlust

Weil Yakon Flows **über mehrere Interaktionen hinweg leben** (Generator!), kann eine KI einen Multi-Step-Dialog führen:

```
Mensch: "Ich möchte eine Rechnung schreiben"
  → KI startet Flow: billing/invoice create
  → System fragt: "Firma?"
  → KI: "ACME Corp"
  → System fragt: "Betrag?"
  → KI: "490,00"
  → Flow endet, Rechnung erstellt
```

Ohne Session-Management, ohne State-Rekonstruktion, ohne API-Endpunkt-Hopping.

---

## 7. Zusammenfassung

| Aspekt | Klassisch | Yakoon |
|--------|-----------|--------|
| **Mensch-Interface** | GUI/CLI | InputEvent → Node-Baum |
| **Maschinen-Interface** | REST/GraphQL/gRPC | InputEvent → Node-Baum |
| **KI-Interface** | AI Agent SDK | InputEvent → Node-Baum |
| **Auth Mensch** | Session/Password | PermissionChecker via Ports |
| **Auth KI** | API-Key/OAuth | PermissionChecker via Ports |
| **Output Mensch** | HTML/Rich-Text | Projection |
| **Output Maschine** | JSON/Protobuf | Projection |
| **Output KI** | Proprietär | Projection |
| **Multi-Step** | State-Machine/Saga | Flow (Python-Generator) |
| **Selbstbeschreibung** | OpenAPI/Dokumentation | Node-Baum (live, autorisiert) |

> **Yakoon hat kein "AI-Problem", weil es kein "Mensch-Problem" hat.**
>
> Es gibt nur **Akteure**, die InputEvents senden und Projections empfangen.
> Die KI ist nur ein weiterer Akteur – kein Sonderfall, keine Extra-API,
> keine Extra-Auth, kein Extra-Output.
>
> **Der Node-Baum ist die API. Für alle.**
