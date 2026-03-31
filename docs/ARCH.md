# SAM = Event-driven state machine with deterministic projection
*SAM ist eine wahrnehmbare Zustandsmaschine*
---

## 2026-03-31
**UI vs SAM**
*UI-System denkt:*
- Buttons
- Screens
- Layout
*SAM denkt:*
- Zustand
- Übergänge
- Entscheidungen

## 2026-03-31
**Was ist der Flow**
Der Flow ist die einzige Quelle von Wahrheit.
Die Projection ist eine deterministische Funktion dieses Zustands.
- UI existiert nicht — sie entsteht aus State
*nicht:*
- „zeige Button“
- „öffne Dialog“
*sondern:*
- „Zustand ist jetzt so“

## 2026-03-31
**Prozess & Zustand & Projektion**
Der Prozess bestimmt den Zustand
Der Zustand bestimmt die Projection
Die Projection bestimmt die UI
Bedeutet:
- Flow - State Machine
- Projector - Pure Funktion => projection = f(State)
- Projection - Materialisierte Sicht auf den Zustand

## 2026-02-21
**Was wir bauen, hat tatsächlich Kernel-Eigenschaften:**
Ein Kernel:
- koordiniert Abläufe
- verwaltet Zustand
- kontrolliert Blockierung
- delegiert Darstellung
- bleibt selbst UI-agnostisch
Unsere Runtime macht exakt das:
- Queue = Scheduling
- WorkflowService = Prozess-Orchestrierung
- DialogService = Blocking-State
- Session = Kontext
- Host = Adapter

Das ist strukturell näher an einem Betriebssystemkern als an einer CRUD-App.
