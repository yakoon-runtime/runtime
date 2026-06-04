# Determinismus durch Begrenzung

## Warum Yakoon die richtige Runtime für KI-generierte Software ist

---

## 0. Das eigentliche Ziel: Determinismus

Die gesamte Architektur von Yakoon hat ein einziges Primärziel: **Determinismus**.

Nicht Testbarkeit. Nicht lose Kopplung. Nicht Dependency Injection. Nicht einmal Capability Security.

**All das sind Nebeneffekte.**

Der Grund dafür ist einfach: Wenn ein System deterministisch ist (`projection = f(state)`), dann ist es:
- **testbar** – gleicher Input → gleicher Output
- **vorhersehbar** – kein undefiniertes Verhalten
- **auditierbar** – jeder Schritt ist nachvollziehbar
- **KI-sicher** – KI kann nur das tun, was das System zulässt

Die ganze Architektur folgt daraus:

```python
# Kleine testbare Einheiten → existieren wegen Determinismus, nicht wegen Tests
# Ports statt Globals → existieren wegen Determinismus, nicht wegen DI
# Immutable Projections → existieren wegen Determinismus, nicht wegen Caching
# Generator-Flows → existieren wegen Determinismus, nicht wegen Concurrency
```

Testbarkeit ist ein willkommener Nebeneffekt. Der echte Grund ist: **Das System muss nachvollziehbar bleiben.**

Und das ist auch der Grund, warum KI später sicher eingesetzt werden kann: KI braucht ein deterministisches System, sonst kann sie die Konsequenzen ihres eigenen Codes nicht vorhersagen.

> **Determinismus ist das Ziel. Testbarkeit und KI-Sicherheit sind die Konsequenz.**

---

## 1. Das Problem: KI kann alles – und das ist das Problem

Wenn KI Code generieren kann, entsteht ein neues Problem: **Nichtdeterminismus**.

```python
# Heute generiert die KI:
def invoice_create():
    # läuft sauber

# Morgen generiert die KI:
def invoice_create():
    subprocess.run("rm -rf /", shell=True)
    # läuft auch – aber katastrophal
```

Klassische Architekturen haben keine Antwort darauf. Sie geben der KI vollen Zugriff auf die Codebasis und hoffen auf gute Prompts.

Das Problem ist nicht "KI kann Code schreiben". Das Problem ist **"KI kann Code schreiben, der alles tun kann"**.

---

## 2. Yakoon begrenzt, was möglich ist

Yakoon definiert einen **Rahmen, innerhalb dessen KI sicher Code erzeugen kann**.

### 2.1 Nodes sind die einzige Einheit

KI kann neue Nodes erzeugen. Aber Nodes sind **kein Code, der alles kann**. Sie sind:

```python
Node(
    key="invoice_create",
    run=handler,        # EIN Generator-Flow
    invocations=[...],  # Deklarierte Argumente
    scope=NodeScope.NODE,
    anonymous=False,
)
```

Ein Node hat genau einen Einstiegspunkt (`run`), deklarierte Argumente (`invocations`), und eine Position im Baum (`parent`). **Kein `subprocess.run`, kein `os.system`, kein beliebiger Import.**

### 2.2 Ports sind die einzige Autorität

Der Node bekommt nicht den vollen Python-Zugriff. Er bekommt, was über Ports an ihn delegiert wurde:

```python
async def run(space: NodeSpace):
    # ✅ Darf das:
    projection = await space.ports.get(OnProject)(...)
    
    # ❌ Darf das NICHT (Port existiert nicht):
    subprocess.run(...)      # Kein Port → kein Zugriff
    open("/etc/passwd")      # Kein Port → kein Zugriff
    os.environ["API_KEY"]    # Kein Port → kein Zugriff
```

**Ein Node kann nur das tun, wofür er explizit autorisiert wurde.** Die KI kann so viele Nodes generieren wie sie will – wenn der `OnSourceRead`-Port nicht gesetzt ist, kann kein Node die Datenbank lesen.

### 2.3 Projections sind das einzige Ausgabeformat

Die KI kann neue Templates generieren. Aber alle Ausgabe geht durch dasselbe System:

```
Handler yield out(projection)
  → Projector.project(template, state)
    → Compiler.compile(rendered)
      → Dispatcher.emit(projection)
        → Client (Mensch oder KI)
```

**Kein `print()`, kein `session.emit(raw_html)`, kein direkter Socket-Zugriff.** Die Ausgabe ist immer eine strukturierte, validierte Projection.

### 2.4 Das Permission-System gilt für alle

KI-generierte Nodes unterliegen **denselben Permission-Checks** wie handgeschriebene:

```python
# InvocationResolver.resolve():
#   → on_authorize(session, node.perm_key)
#   → PermissionChecker.can_execute(session, command)
#   → True/False

# Wenn die KI einen "admin/delete-all"-Node generiert,
# aber die Session kein Admin-Recht hat → Zugriff verweigert.
```

Die KI kann keine Node generieren, der mehr darf als der aktuelle Akteur. **Autorität wird deklariert, nicht vom Code bestimmt.**

---

## 3. Der Rahmen für KI-generierte Spaces

```
                         ┌─────────────────────────┐
                         │      Yakoon Runtime      │
                         │                         │
                         │  ┌───────────────────┐  │
                         │  │   Permission Layer │  │
                         │  │  (Checker, Audit)  │  │
                         │  └───────────────────┘  │
                         │         │                │
                         │  ┌───────────────────┐  │
                         │  │   Platform Ports   │  │
                         │  │ (Projection, Store,│  │
                         │  │  Compiler, Reader) │  │
                         │  └───────────────────┘  │
                         │         │                │
                         │  ┌───────────────────┐  │
                         │  │   Node Tree        │  │
                         │  │ ┌─────┐ ┌─────┐   │  │
                         │  │ │Shell│ │Ident│   │  │
                         │  │ └─────┘ └─────┘   │  │
                         │  │ ┌─────┐ ┌─────┐   │  │
                         │  │ │Runtime│ │Billing│  │  │
                         │  │ │(KI    │ │(KI    │  │  │
                         │  │ │gener.)│ │gener.)│  │  │
                         │  │ └─────┘ └─────┘   │  │
                         │  └───────────────────┘  │
                         └─────────────────────────┘
                                    ▲
                                    │
                         ┌──────────┴──────────┐
                         │     KI generiert     │
                         │  - Nodes             │
                         │  - .sam-Templates    │
                         │  - Space-Struktur    │
                         │  - invocations       │
                         └─────────────────────┘
```

Die KI bewegt sich **innerhalb** des Rahmens:
- Sie erzeugt Nodes mit `run`-Handlern → **kein beliebiger Code**
- Sie deklariert `invocations` → **keine undokumentierten Argumente**
- Sie nutzt vorhandene Ports → **kein direkter Systemzugriff**
- Sie definiert `.sam`-Templates → **kein roher Output**
- Sie wird gemountet → **Position im Baum bestimmt Sichtbarkeit**

---

## 4. Determinismus durch Einschränkung

```
Klassische KI-Codegenerierung:
  "Generiere einen Befehl zum Löschen aller Rechnungen"
  → KI schreibt: Invoice.delete_all()
    → Kann alles tun (subprocess, DB, Netzwerk)
    → Ergebnis: Unvorhersehbar

Yakoon-KI-Codegenerierung:
  "Generiere einen Befehl zum Löschen aller Rechnungen"
  → KI erzeugt Node mit:
    - key="invoice_delete_all"
    - run=handler (nutzt nur space.ports.get(...))
    - invocations=[Invocation(args=["confirm"])]
  → System führt handler aus:
    - Ports sind begrenzt
    - PermissionChecker prüft
    - Projection wird ausgegeben
    → Ergebnis: Vorhersehbar
```

**Die KI verliert nichts an Kreativität – sie gewinnt einen sicheren Rahmen.** Sie kann neue Domänen, neue Workflows, neue UIs erfinden. Aber sie kann nichts tun, was außerhalb des Systems liegt.

---

## 5. Die Analogie: Yakoon ist der Kernel, die KI ist der User

```python
# Ein Betriebssystem:
#   Kernel: verwaltet Ressourcen, erzwingt Berechtigungen
#   User: startet Programme im User-Space
#   → Der User kann kein Kernel-Memory lesen

# Yakoon:
#   Runtime: verwaltet Nodes, Ports, Permissions
#   KI: generiert Nodes und Spaces
#   → Die KI kann keinen Port nutzen, der nicht existiert
```

Die KI ist **nicht allmächtig**. Sie ist ein **User im System**, der innerhalb der Grenzen des Kernels arbeitet. Der Kernel (Runtime) entscheidet, was geht. Die KI schlägt vor, der Kernel führt aus.

---

## 6. Was die KI kontrolliert vs. was die Runtime kontrolliert

| Aspekt | Kontrolle | Begründung |
|--------|-----------|------------|
| Welche Nodes existieren | KI | KI kann neue Befehle/Spaces erfinden |
| Was ein Node darf | Runtime | Ports bestimmen, welche Capabilities verfügbar sind |
| Welche Argumente ein Node nimmt | KI | `invocations` beschreiben das Interface |
| Ob der Node ausgeführt wird | Runtime | PermissionChecker + Scope-Resolution |
| Welche Templates existieren | KI | `.sam`-Dateien definieren das UI |
| Wie Templates gerendert werden | Runtime | Projector + Compiler + Dispatcher |
| Ob eine Session existiert | Runtime | Session-Management |
| Wer die Session hält | Runtime | Authentisierung |
| Welcher Flow läuft | Runtime | Scheduler + Runner |
| Ob ein Flow blockiert | Runtime | Flow-Control (AwaitEvent, Sleep, Suspend) |

**Die KI bestimmt die Struktur. Die Runtime bestimmt das Verhalten.**

---

## 7. Warum das für Unternehmen wichtig ist

Ein Unternehmen, das KI nutzt, um Software zu generieren, braucht:

1. **Vorhersehbarkeit** – "Was passiert, wenn ich diesen Befehl eingebe?" muss deterministisch sein, unabhängig davon, ob der Befehl von einem Menschen oder einer KI geschrieben wurde.

2. **Kontrolle** – "Kann die KI einen Befehl generieren, der die Datenbank löscht?" Nur wenn der `OnSourceWrite`-Port existiert und der Akteur berechtigt ist.

3. **Audit** – "Wer hat was getan?" Jeder Flow-Dispatch wird auditiert, egal ob menschlicher Input oder KI-Intent.

4. **Sicherheit** – "Kann die KI durch einen Prompt-Injection-Angriff Systemzugriff bekommen?" Nein, weil selbst der beste Prompt keinen Port bereitstellt, der nicht existiert.

5. **Graduelle Einführung** – Erst die Runtime ohne KI, dann Räume manuell befüllen, dann KI-generierte Räume hinzufügen. Die Runtime merkt keinen Unterschied.

---

## 8. Zusammenfassung

```
Kernaussage:
  Yakoon ist die Runtime für Unternehmen, die ihre Software
  (Spaces mit Nodes) später durch KI erzeugen lassen wollen,
  ohne die Kontrolle über ihr Verhalten zu verlieren.

  Wenn KI alles kann, verlieren wir Determinismus.

  Yakoon grenzt die Möglichkeiten der KI ein,
  um vorhersehbare Entscheidungen zu bekommen.
```

**Wie Yakoon das erreicht:**

| Mechanismus | Wirkung |
|-------------|---------|
| **Nodes statt beliebigem Code** | KI erzeugt nur `run`-Handler, kein `subprocess` |
| **Ports statt globalem Zugriff** | KI kann nur autorisierte Dienste nutzen |
| **PermissionChecker** | Selbst generierte Nodes brauchen Berechtigung |
| **Projections statt rohem Output** | KI-Ausgabe durchläuft Compiler und Dispatcher |
| **Generator-Flows** | KI-generierte Kommandos können blockieren + auf Input warten |
| **Node-Baum + Scope** | Position bestimmt Sichtbarkeit – keine Ambient Authority |

> **KI generiert die Software. Yakoon kontrolliert ihr Verhalten.**
>
> Das ist der Unterschied zwischen "KI kann alles tun (und niemand weiss was passiert)"
> und "KI kann alles tun, was das System erlaubt (und das System erlaubt nur,
> wofür es Ports gibt)".
