# OCap-Analyse: Yakoon Ports-System

## Object-Capability vs. Yakoon

---

## 1. Kernprinzipien von Object-Capability-Systemen

| Prinzip | Beschreibung |
|---------|-------------|
| **Keine Ambient Authority** | Autorität ist nur erreichbar, wenn man eine Referenz darauf hält |
| **Nur Konnektivität erzeugt Konnektivität** | Man kann nur das aufrufen, wofür man eine direkte Referenz hat |
| **POLA (Principle of Least Authority)** | Jedes Objekt bekommt genau die minimale Autorität, die es braucht |
| **Kapselung** | Privater Zustand ist nur über definierte Methoden zugänglich |
| **Keine Allmacht-Zentrale** | Es gibt keinen Hintertür-Zugang zu globalen Ressourcen |

---

## 2. Vergleich mit etablierten OCap-Systemen

### 2.1 E Language

**E** ist eine reine OCap-Sprache. Alle Werte sind Objekte, alle Objekte haben Referenzen, es gibt keine Ambient Authority.

| Aspekt | E | Yakoon |
|--------|---|--------|
| **Referenzmodell** | Near-References (gleiche Vat) / Far-References (Vat-übergreifend) | Protocol-typisierte Lookups (`ports.get(ProtocolType)`) |
| **Autorität** | Nur durch gehaltene Referenzen | Hierarchische Vererbung + Backdoors |
| **Capability-Erwerb** | Referenz muss übergeben werden | Typ-Lookup in Container-Kette |
| **Sicherheit** | Formal verifizierbar | Keine formalen Garantien |

**E-Prinzip:** Man kann ein Objekt NUR aufrufen, wenn man eine Referenz darauf hat. Es gibt keinen "Namen" oder "Pfad", unter dem man es finden könnte – nur Referenzen.

**Yakoon-Verletzung:** `ports.get(OnProjectionResolve)` ist ein **Typ-indizierter Lookup** – kein Referenz-Handling. Jeder Node kann nach jedem Typ fragen; die Container-Kette entscheidet, ob er ihn bekommt. In E müsste man die Projektions-Funktion als Referenz übergeben bekommen haben.

### 2.2 KeyKOS

**KeyKOS** ist ein Capability-basiertes Betriebssystem. Prozesse kommunizieren über "Keys" (Capabilities), und der Kernel vermittelt jeden Zugriff.

| Aspekt | KeyKOS | Yakoon |
|--------|--------|--------|
| **Autoritätsträger** | Kernel-verwaltete Keys (unfälschbar) | Python-Objekt-Referenzen |
| **Durchsetzung** | Hardware/Kernel (erzwungen) | Keine (reine Konvention) |
| **Widerruf** | Key-Redirection (first-class) | Nicht vorhanden |
| **Typdomänen** | Getrennte System-/App-Keys | Ein flacher Namensraum pro Container |

**KeyKOS-Prinzip:** Keys sind unfälschbar und nur durch den Kernel verwaltbar. Man kann KEINEN Key bekommen, außer man hat ihn explizit erhalten.

**Yakoon-Verletzung:** `node.root.ports.get(...)` ist ein **Ambient-Backdoor** – ein tiefer Node kann ohne explizite Autorisierung alle Root-Capabilities erreichen. In KeyKOS müsste man dafür einen Key zum Root-Prozess besitzen.

### 2.3 Caja

**Caja** ist ein JavaScript-Subset, das OCap-Regeln durch einen statischen Verifizierer ("Cajita" + "Whitelist") durchsetzt.

| Aspekt | Caja | Yakoon |
|--------|------|--------|
| **Isolation** | Membranen um unvertrauten Code | Keine (Nodes teilen denselben Python-Prozess) |
| **Versiegelung** | `Object.freeze()`, `seal()` | Nicht vorhanden |
| **Durchsetzung** | Statische Verifikation + Laufzeit-Membranen | Reine Konvention (keine Durchsetzung) |
| **Transformation** | "Cajoler" transformiert Code | Keine |

**Caja-Prinzip:** Vertrauenswürdiger Code wird durch Membranen isoliert. Ein Modul kann nur das tun, wofür die Membran ihm explizit eine Referenz gibt.

**Yakoon-Verletzung:** `Node.parent` und `Node.children` sind **öffentlich und mutierbar** (`node.py:102-103`). Jeder Code, der eine Node-Referenz hat, kann `node.parent.parent.children["root"].ports.get(...)` aufrufen. Caja würde diese Felder einfrieren oder hinter einer Membran verstecken.

### 2.4 Pony

**Pony** hat ein typsystem-basiertes Capability-System in der Sprache: `ref`, `val`, `iso`, `trn`, `tag` kontrollieren, welche Operationen auf Referenzen erlaubt sind.

| Aspekt | Pony | Yakoon |
|--------|------|--------|
| **Capability-Ebene** | Typsystem (Compile-Zeit) | Architektur (Runtime) |
| **Zweck** | Speichersicherheit + Daten-Race-Freiheit | Autorisierung + Dependency Injection |
| **Durchsetzung** | Compiler (erzwungen) | Keine (Konvention) |
| **Granularität** | Lese-/Schreib-/Aliasing-Rechte pro Referenz | Ganze Dienste pro Port |

**Pony-Prinzip:** Der Compiler erzwingt, dass `iso`-Referenzen nicht geteilt werden, `val`-Referenzen nicht mutiert werden usw. Das verhindert Data Races und Aliasing-Bugs.

**Yakoon-Unterschied:** Yakoon hat kein Typsystem für Capabilities. Ein `get(OnSourceRead)` liefert die Funktion – der Empfänger kann sie beliebig weiterreichen, aufrufen, mutieren (wenn das Objekt mutierbar ist). Pony würde hier Reference Capabilities durchsetzen.

---

## 3. Wo Yakoon OCap-Prinzipien folgt

### 3.1 Hierarchische Delegation via `fork()`

```python
def add(self, child):
    child.ports = self.ports.fork()  # Kind erbt Scope des Eltern-Nodes
```

Ein Kind sieht nur das, was seine Vorfahren explizit per `provide()` registriert haben. Das ist **POLA durch Baumstruktur** – Capabilities fließen entlang struktureller Verbindungen nach unten, nicht durch ein globales Medium.

### 3.2 Richtungsgebundener Capability-Transfer

- `provide()` → delegiert Autorität **nach unten** an Kinder
- `publish()` → exportiert Autorität **nach oben** an den Eltern-Node

Das spiegelt das OCap-Prinzip wider, dass Autorität sich entlang expliziter struktureller Verbindungen bewegt, nicht durch einen "Äther".

### 3.3 Kein globaler Singleton-Registry

Es gibt kein `service_locator.get("db")`. Capabilities werden auf spezifische Nodes im Baum verdrahtet und strukturell vererbt. Wenn ein Node nicht unter dem Root sitzt, der `OnProjectionResolve` hat, kann er nicht projizieren – es gibt keinen Hinterkanal.

### 3.4 `mount()` bewahrt Subtree-Autonomie

```python
def mount(self, parent):
    self._local.mount(parent._local)    # Lookup nach oben erweitern
    self._publish_to = parent._local    # Publikationen in Eltern-Container
```

Ein gemounteter Space (z.B. `y5nspace-ident`) behält seine interne Capability-Struktur. Der Eltern-Node kann NICHT in die privaten Capabilities des Kindes greifen – nur das, was das Kind explizit per `publish()` nach oben gibt. Das ist **gekapselte Autorität**.

### 3.5 Protokolle als Capability-Interfaces

Ports sind getypte `Protocol`-Klassen, keine String-Keys. Das bietet nominelle Struktur – man kann einen Protocol-Type nicht "erraten", wie man einen String-Key erraten könnte.

---

## 4. Wo Yakoon OCap-Prinzipien verletzt

### 4.1 `node.root` – Ambient Backdoor

**Datei:** `runtime/y5ncore-base/src/y5n/base/nodes/node.py:169-195`

```python
@property
def root(self) -> Node:
    node = self
    while node.parent is not None:
        node = node.parent
    return node
```

Jeder Node kann zum Root laufen und **alle** Root-Capabilities abrufen:

```python
# runtime/y5ncore-runtime/src/y5n/runtime/wire/machine.py:77
on_error = node.root.ports.get(OnErrorResolve)  # Ambient!
```

Ein tiefer Leaf-Node, der nichts mit Projektion zu tun hat, kann `node.root.ports.get(OnProjectionResolve)` aufrufen. In einem echten OCap-System müsste das Erreichen der Baumspitze selbst eine Capability erfordern.

**Bewertung: KRITISCHE Verletzung**

### 4.2 `ports_from()` – Außer-Band-Auflösung

**Datei:** `runtime/y5ncore-base/src/y5n/base/nodes/node.py:227-265`

```python
# spaces/y5nspace-shell/.../man.py:46
ports = space.ports_from(path=found["path"], absolute=True)
```

Löst die Ports eines **anderen** Nodes per Pfadnamen auf, statt per Referenz. In OCap: **Nur Konnektivität erzeugt Konnektivität**. Wenn man `"../sibling/sub/node"` auflösen und dessen Ports abgreifen kann, hat man ambient Navigation, nicht Capability-sicheren Zugriff.

**Bewertung: KRITISCHE Verletzung**

### 4.3 Mutable `parent` und `children`

**Datei:** `runtime/y5ncore-base/src/y5n/base/nodes/node.py:102-103`

```python
parent: Node | None = None
children: dict[str, Node] = field(default_factory=dict)
```

Beide Felder sind öffentlich und mutierbar. Jeder Code mit einer Node-Referenz kann:

```python
node.parent.parent.children["root"].ports.get(...)  # beliebiger Baumdurchlauf
```

Das gewährt **ambienten Zugriff auf die gesamte Hierarchie**.

**Bewertung: SCHWERE Verletzung**

### 4.4 `Node.find()` mit `..`-Traversal

**Datei:** `runtime/y5ncore-base/src/y5n/base/nodes/node.py:326-334`

```python
if part == "..":
    if current.parent:
        current = current.parent  # beliebig nach oben
```

Kombiniert mit `ports_from()` kann jeder Command-Handler den Baum per Namen durchlaufen und Capabilities aus beliebigen Nodes extrahieren. Verletzt **Nur Konnektivität erzeugt Konnektivität**.

**Bewertung: SCHWERE Verletzung**

### 4.5 Kein Widerruf (Revocation)

Einmal per `provide()` registriert, lebt die Capability für immer in der Container-Kette. Alle Kinder, die geforkt haben, behalten Zugriff. Kein Weg zu widerrufen, in einen Proxy zu wrappen oder zu attenuieren. In E/KeyKOS ist Widerruf via Forwarder ein First-Class-Pattern.

**Bewertung: MITTLERE Verletzung**

### 4.6 Typ-indiziertes Lookup statt Objekt-Referenz

```python
space.ports.get(Namespaces)     # Lookup per TYP
space.ports.get(OnProject)      # Lookup per PROTOKOLL
```

In echtem OCap (E, KeyKOS) sind Capabilities **Objekt-Referenzen**. Man kann nur das aufrufen, wofür man eine Referenz hält. Yakoon verwendet einen **typ-indizierten hierarchischen Service Locator** – besser als global, aber immer noch *Lookup per Typ*, nicht *Aufruf per Referenz*. Ein Node kann nach *jedem* Typ fragen; die Container-Kette entscheidet, ob er ihn bekommt.

**Bewertung: MITTLERE Verletzung** (Design-Entscheidung, kein Bug)

### 4.7 Capability-Proliferation via `fork()`

```python
def fork(self) -> NodePorts:
    return NodePorts(
        publish_to=self._local,
        local=self._local.fork(),  # Kind sieht Eltern-Container als Parent
    )
```

Wenn der Eltern-Node **nach** dem Fork neue Capabilities hinzufügt, sieht das Kind sie automatisch (via Eltern-Container-Kette). In echtem OCap werden Capabilities zum Zeitpunkt der Erzeugung übergeben; nachträgliche Sichtbarkeit ist Ambient Authority.

**Bewertung: MITTLERE Verletzung**

### 4.8 Keine Isolation/Confinement

Wenn ein Node eine Capability per `get()` erhält, kann er sie beliebig an andere Nodes weitergeben (per `publish()` oder als Funktionsargument). Es gibt keine Taint-Verfolgung, keine Membranen, keine "diese Capability kam von einem weniger vertrauenswürdigen Node"-Durchsetzung. Caja bietet dies via Membranen; Yakoon hat nichts dergleichen.

**Bewertung: MITTLERE Verletzung**

---

## 5. Zusammenfassung

| Aspekt | E Language | KeyKOS | Caja | Pony | Yakoon |
|--------|-----------|--------|------|------|--------|
| **Referenzmodell** | Near/Far-Refs | C-List Keys | Getamte JS-Refs | Ref-Caps (iso/val/trn) | Protocol-typisiertes Lookup |
| **Ambient Authority?** | Keine | Keine | Keine (getamt) | Keine (typerzwungen) | **Ja** (`root`, `..`, `children`) |
| **Pfad-Traversal?** | Keines | Keines | Keines (getamt) | Keines | **Ja** (`find()`, `ports_from()`) |
| **Widerruf?** | Vat-Pivot | Key-Redirection | Membrane | Actor-Lifecycle | **Nein** |
| **Confinement?** | Vat-basiert | Domain-basiert | Membranen | Cap-secure Typen | **Nein** |
| **Durchsetzung** | Sprache | Kernel | Verifizierer | Compiler | **Konvention (keine)** |
| **Mutabilität** | Near-Refs mutierbar, aber nicht traversierbar | Keys immutabel | Freeze/Seal | Iso/val/trn erzwungen | **Public mutable `parent`/`children`** |

### Bewertungsskala

| Kap | Bewertung |
|-----|-----------|
| `node.root` | ❌ **Kritisch** – Ambient-Authority-Backdoor |
| `ports_from()` | ❌ **Kritisch** – Pfadbasierte Capability-Extraktion |
| `parent`/`children` mutable | ❌ **Schwer** – Beliebige Baumtraversierung |
| `find(..)` mit `..` | ❌ **Schwer** – Aufwärtstraversal |
| Kein Widerruf | ⚠️ **Mittel** – Fehlende OCap-Funktion |
| Typ-Lookup statt Referenz | ⚠️ **Mittel** – Design-Entscheidung |
| `fork()` post-hoc Visibility | ⚠️ **Mittel** – Leaking Authority |
| Kein Confinement | ⚠️ **Mittel** – Fehlende Isolation |
| Hierarchische Delegation | ✅ **Folgt OCap** |
| `provide`↓/`publish`↑ | ✅ **Folgt OCap** |
| Kein globaler Singleton | ✅ **Folgt OCap** |
| `mount()`-Autonomie | ✅ **Folgt OCap** |
| Protokolle als Interfaces | ✅ **Folgt OCap** |

---

## 6. Fazit: Capability-Inspiriert, nicht Object-Capability

Yakoons Port-System sitzt zwischen **hierarchischem DI** und **Object-Capability Security**:

**Was es richtig macht:**
- OCap-artige Delegation (`fork`/`mount`)
- Richtungsabhängiger Capability-Fluss (`provide`↓/`publish`↑)
- POLA durch Baumstruktur
- Kein globaler Service Locator

**Was es untergräbt:**
- Ambient Backdoors (`root`, `Node.find(..)`)
- Mutable `parent`/`children` Felder
- Pfadbasierte Capability-Extraktion (`ports_from(path)`)
- Keine Isolation/Durchsetzung

### Was sich ändern müsste für echtes OCap

1. **`node.root` entfernen** – das Erreichen des Roots müsste eine explizite Capability erfordern
2. **`ports_from(path)` entfernen** – Capability-Auflösung per Pfad verletzt referenzbasierte Sicherheit
3. **`parent` und `children` einfrieren** – keine ambienten Baumdurchläufe
4. **`..` in `find()` entfernen** – Aufwärtstraversal darf es nicht geben
5. **Widerruf einbauen** – Capability-Proxies/Forwarder
6. **Capabilities als Referenzen, nicht Typen** – statt `ports.get(ProtocolType)` konkrete Callables/Referenzen injizieren
7. **Isolation/Confinement für Plugins** – Membranen um nicht-vertrauenswürdige Spaces

### Kontext

Die Architektur ist für **strukturelle Autoritätsdelegation** entworfen, nicht für **Sicherheits-Confinement**. Wenn niemals nicht-vertrauenswürdige Plugins im selben Baum laufen, sind die Backdoors irrelevant. Aber das System kann POLA auf Object-Capability-Ebene nicht formal garantieren – es ist ein **Capability-inspiriertes DI-System**, kein **Object-Capability-System**.
