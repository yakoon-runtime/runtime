# Aufwand für neue Funktionen und Domänen

## Vergleich mit anderen Runtimes

---

## 1. Neue Funktion (einzelnes Kommando)

Beispiel: `uptime` – zeigt an, wie lange das System läuft.

### Dateien und Zeilen

| Schritt | Datei | Zeilen | Code |
|---------|-------|--------|------|
| Handler schreiben | `runtime/uptime.py` | ~20 | `async def run(space):` + Logik + `yield out(projection)` |
| Node registrieren | `space.py` | 6 | `runtime.add(Node(key="uptime", run=uptime, ...))` |
| Template erstellen | `resources/de/templates/uptime/result.sam` | ~8 | Jinja2 + `<kv>`-Blöcke |
| **Total** | **3 Dateien** | **~34** | |

**Aufwand:** ~30 Minuten für einen Yakoon-entwickler.

### Code-Beispiel

```python
# runtime/uptime.py
async def run(space: NodeSpace):
    projection = await space.ports.get(OnProject)(
        name="uptime/result",
        lang=space.session.lang,
        state={"uptime": _get_uptime()},
    )
    yield out(projection)
```

```python
# in space.py
runtime.add(Node(key="uptime", run=uptime, anonymous=True))
```

```xml
<!-- resources/de/templates/uptime/result.sam -->
<h1>Systemlaufzeit</h1>
<kv>
  <item key="Laufzeit">{{ state.uptime }}</item>
  <item key="Gestartet vor">{{ state.started }}</item>
</kv>
```

### Was muss der Entwickler NICHT tun?

- Kein URL-Routing (`@app.get("/uptime")`)
- Keine Serializer/Request-Validation (Pydantic/attrs)
- Keine Response-Envelopes (`{"status": "ok", "data": ...}`)
- Kein Client-Code (das Rendering passiert serverseitig)
- Keine Middleware (Auth fliesst via Ports)
- Keine Datenbank-Connection (wenn nicht benötigt)
- Keine Session-Verwaltung (bereits im `space.session`)

---

## 2. Neue Domäne

Beispiel: Domäne "Billing" – Rechnungen, Zahlungen, Abos.

### Paketstruktur

```
spaces/y5nspace-billing/
├── pyproject.toml                  # 10 Zeilen
├── src/y5nspace/billing/
│   ├── __init__.py
│   ├── space.py                    # 25 Zeilen: Node-Baum
│   ├── ports.py                    # 20 Zeilen: Port-Protokolle
│   ├── runtime/
│   │   ├── __init__.py
│   │   ├── setup.py                # 40 Zeilen: Wiring
│   │   ├── invoice/
│   │   │   ├── __init__.py
│   │   │   ├── space.py            # 10 Zeilen: Sub-Node
│   │   │   ├── list.py             # 25 Zeilen: Handler
│   │   │   ├── show.py             # 30 Zeilen: Handler
│   │   │   └── pay.py              # 50 Zeilen: Handler (Flow!)
│   │   ├── subscription/
│   │   │   ├── __init__.py
│   │   │   ├── space.py            # 10 Zeilen
│   │   │   └── manage.py           # 60 Zeilen: Handler (Flow!)
│   │   └── payment/
│   │       ├── __init__.py
│   │       └── process.py          # 40 Zeilen: Handler
│   ├── services/
│   │   ├── __init__.py
│   │   ├── invoice_service.py      # 80 Zeilen: Business Logic
│   │   ├── payment_service.py      # 60 Zeilen
│   │   └── subscription_service.py # 100 Zeilen
│   └── resources/
│       └── de/
│           └── templates/
│               ├── invoice/list.sam     # 15 Zeilen
│               ├── invoice/show.sam     # 20 Zeilen
│               ├── invoice/pay.sam      # 25 Zeilen
│               ├── subscription/manage.sam # 20 Zeilen
│               └── payment/process.sam  # 15 Zeilen
├── tests/
│   ├── test_invoice.py
│   └── test_services.py
```

### Aufwandsschätzung

| Komponente | Einfach | Mittel | Komplex |
|-----------|---------|--------|---------|
| Node-Baum (`space.py`) | 15 Min | 30 Min | 1 Std |
| Port-Protokolle (`ports.py`) | 15 Min | 30 Min | 1 Std |
| Handler pro Befehl | 20 Min | 45 Min | 2 Std |
| `.sam`-Template pro Ansicht | 15 Min | 30 Min | 1 Std |
| Setup/Wiring | 30 Min | 1 Std | 2 Std |
| Services (Business-Logik) | – | 2 Std | 8 Std |
| Tests | 1 Std | 3 Std | 8 Std |
| **Total** | **~3 Std** | **~1 Tag** | **~3 Tage** |

### Integration in die Plattform

Nachdem die Domäne geschrieben ist:

```bash
# 1. pip install (1 Zeile in install.sh)
pip install -e spaces/y5nspace-billing

# 2. In runtime.py mounten (1 Zeile)
platform.mount(billing)

# 3. Fertig.
```

Der `setup()`-Handler des Billing-Space kümmert sich um alle Ports und Abhängigkeiten. Der Root muss nichts über die innere Struktur wissen.

---

## 3. Vergleich mit anderen Runtimes

### REST-API (FastAPI + SQLAlchemy + Pydantic)

Für eine neue Entität "Invoice":

```python
# models.py (30 Zeilen)
class Invoice(Base): ...

# schemas.py (20 Zeilen)
class InvoiceIn(BaseModel): ...
class InvoiceOut(BaseModel): ...

# router.py (40 Zeilen)
@router.get("/invoices")
@router.post("/invoices")
@router.get("/invoices/{id}")
@router.put("/invoices/{id}")
@router.delete("/invoices/{id}")

# service.py (50 Zeilen)
class InvoiceService: ...

# tests.py (100 Zeilen)
```

| Aspekt | REST-API | Yakoon |
|--------|----------|--------|
| **CRUD-Boilerplate** | Hoch (5 Endpoints, Serializer, Model) | Niedrig (nur das, was wirklich gerendert wird) |
| **Server-Client-Vertrag** | Serializer + Client-Modelle | Serverseitig (kein Client-Code) |
| **Live-Updates** | WebSocket extra bauen | Eingebaut (Flow + Projection) |
| **Multi-Step-Interaktion** | Session-State selbst verwalten | Eingebaut (Generator-Flows) |
| **Formular-Validierung** | Pydantic + JS-Validation | Policy-System + server-seitig |
| **Authentisierung** | Middleware + JWT | Port-basiert (PermissionChecker) |
| **Dokumentation** | OpenAPI/Swagger (automatisch) | Manual-Resource (manuell) |

**Fazit REST-API:** Yakoon ist schneller für interaktive, multi-step UIs. REST ist schneller für reine Daten-CRUD ohne UI.

### Event-Sourcing (EventStoreDB + Axon)

Für eine neue Aggregate "Invoice":

| Schritt | Axon Framework | Yakoon |
|---------|---------------|--------|
| Events definieren | 3-5 Klassen | Keine (EntityStore) |
| Aggregate schreiben | 100-200 Zeilen | Kein separates Aggregate |
| Command Handler | 30-50 Zeilen | Flow-Handler (50-80 Zeilen) |
| Event Handler/Projection | 50-100 Zeilen | `.sam`-Template (15-20 Zeilen) |
| Repository | Automatisch | EntityStore (bereits da) |
| Saga/Prozess-Manager | 100-200 Zeilen | Flow (eingebaut, Generator!) |
| Event-Upgrade | Migration-Skript | Patch-Strategie (JsonPatch) |

**Fazit Event-Sourcing:** Yakoon ist schneller für einfache Event-Sourcing-Fälle (kein Aggregate-Boilerplate, kein separates Event-Repository). Axon ist mächtiger für komplexe Event-Upgrades, Snapshots und langlaufende Sagas.

### Chat-Plattform (Rasa/Botpress)

Für einen neuen Intent:

| Schritt | Rasa | Yakoon |
|---------|------|--------|
| NLU-Daten | 10-50 Beispiele pro Intent | Keine (NLU-frei) |
| Story/Flow | Story-Datei | Python-Generator |
| Action | Python-Action-Server | Flow-Handler |
| Response | `respond()` | `yield out(projection)` |
| Slot/State | Slots + Tracking | Generator-Variablen |

**Fazit Chat-Plattform:** Yakoon ist schneller, weil es kein NLU-Training braucht – die Eingabe ist strukturierte Kommandozeile, nicht Free-Text-NLP. Dafür kann Yakoon keine natürliche Sprache verstehen.

### GraphQL (Apollo + TypeGraphQL)

Für einen neuen Resolver:

```typescript
@Resolver(Invoice)
class InvoiceResolver {
  @Query(() => [Invoice])
  async invoices(@Arg("userId") userId: string) { ... }

  @Mutation(() => Invoice)
  async payInvoice(@Arg("id") id: string) { ... }
}
```

| Aspekt | GraphQL | Yakoon |
|--------|---------|--------|
| **Schema-Definition** | Type-Definitionen | `.sam`-Templates |
| **Resolver** | Funktion pro Query/Mutation | Flow-Handler |
| **Client-Anfragen** | Client bestimmt Felder | Server bestimmt Projection |
| **Live-Queries** | Subscriptions (extra) | Eingebaut (Flow) |
| **Lazy Loading** | DataLoader-Pattern | Nicht nötig (serverseitig) |
| **Caching** | Normalisierung (Client) | Projection-Caching (Server) |

**Fazit GraphQL:** Yakoon ist schneller für **server-driven UI** – der Server bestimmt, was der Benutzer sieht. GraphQL ist besser, wenn der Client flexibel sein muss (verschiedene Apps, verschiedene Felder).

### Microservice (Event-basiert, Kafka/NATS)

Für eine neue Domäne:

| Aspekt | Microservice | Yakoon |
|--------|-------------|--------|
| **Service-Grenzen** | Separater Prozess + Docker | In-Process Space |
| **Kommunikation** | Events via Broker | Ports (in-memory, typisiert) |
| **Deployment** | Docker + Orchestrierung | `pip install` + `platform.mount()` |
| **Fehlerisolierung** | Prozessgrenze | Keine (teilt Runtime) |
| **Skalierung** | Horizontal pro Service | Vertikal (grössere Instanz) |

**Fazit Microservice:** Yakoon ist viel schneller für die Entwicklung (keine Deployment-Pipeline, keine Broker-Konfiguration, keine Service-Discovery). Dafür skalieren Microservices besser und isolieren Fehler strikter.

---

## 4. Zusammenfassende Bewertung

### Aufwandsvergleich (neue Domäne "Billing")

| Runtime | Einfach | Mittel | Komplex |
|---------|---------|--------|---------|
| **Yakoon** | **~3 Std** | **~1 Tag** | **~3 Tage** |
| FastAPI REST | ~1 Tag | ~3 Tage | ~1 Woche |
| Axon Event-Sourcing | ~3 Tage | ~1 Woche | ~2 Wochen |
| Rasa Chat | ~2 Tage | ~1 Woche | ~2 Wochen |
| GraphQL (Apollo) | ~1 Tag | ~3 Tage | ~1 Woche |
| Microservice (Kafka) | ~3 Tage | ~1 Woche | ~3 Wochen |

### Yakoon-Stärken (geringerer Aufwand)

| Feature | Warum Yakoon schneller ist |
|---------|---------------------------|
| **Neues Kommando** | Kein Routing, kein Serializer, kein Client-Code |
| **Multi-Step-Interaktion** | Generator pausiert, kein Session-Management nötig |
| **Server-driven UI** | `.sam`-Template statt Client-Code |
| **Event Sourcing** | EntityStore ist fertig, kein Aggregate-Boilerplate |
| **Neue Domäne** | Self-Wiring, keine zentrale Konfiguration |
| **Authentisierung** | PermissionChecker + Ports, keine Middleware |
| **Formularvalidierung** | Policy-System, kein JS |

### Yakoon-Schwächen (höherer Aufwand)

| Feature | Warum Yakoon langsamer ist |
|---------|---------------------------|
| **Reine REST-API** | Yakoon ist nicht dafür gemacht (kein HTTP/JSON-Output) |
| **Mobile App Backend** | Kein JSON-API, nur Streaming-Protokoll |
| **Freitext-Eingabe** | Kein NLU, nur strukturierte Kommandos |
| **Horizontal skalieren** | In-Process Spaces teilen Ressourcen |
| **3rd-Party-Integration** | Kein REST-Client-Generator, kein OpenAPI |
| **Daten-Export** | Projection ist UI-format, nicht Daten-format |

### Wann Yakoon die richtige Wahl ist

```
Server-driven UI mit Multi-Step-Interaktion     →  Yakoon ist optimal
   (Terminal, Web-Terminal, Text-UI)

Reine Daten-CRUD mit JSON-API                   →  FastAPI/Express ist besser
   (Mobile App Backend, SPA)

Komplexes Event Sourcing mit vielen Aggregates   →  Axon/EventStore ist besser
   (Finanzen, Compliance)

Natürlichsprachlicher Chatbot                    →  Rasa ist besser
   (Kunden-Support, Conversational AI)

Hochskalierendes Microservice-System             →  Kafka + Docker ist besser
   (Milliarden Events, viele Teams)
```

### Regel

> **Wenn deine UI interaktiv ist (der Server fragt nach, der User gibt ein), ist Yakoon schneller.**
>
> **Wenn deine UI ein reiner Daten-Client ist (App holt JSON, rendert selbst), ist REST/GraphQL schneller.**
