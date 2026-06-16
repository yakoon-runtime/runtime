# Lokal vs. Web – Warum Yakoon lokal läuft

## Oder: Warum die wertvollsten Daten nicht im Browser liegen

---

## 1. Der Web-First-Irrtum

Die letzten 15 Jahre haben uns erzählt: "Alles muss ins Web. SaaS ist die Lösung. Die Cloud macht's möglich."

Aber: **Im Web hast du keinen Zugriff auf die Daten des Unternehmens.**

```python
# Web-App: Zugriff auf das, was der Browser schickt
async def handle_request(request):
    data = request.json()       # Nur was der User eingetippt hat
    session = request.cookies   # Nur die Session-ID
    # Kein Dateisystem, keine lokale DB, keine internen APIs
```

Eine Web-App ist ein **Sandkasten**. Sie kann nur das tun, was der Browser erlaubt. Deshalb landen Web-Anwendungen früher oder später in einer Cloud – weil sie dort an die Daten kommen.

Aber dann ist die Architektur:
```
Browser → Web-Server → Cloud → API → Datenbank
         (öffentlich)  (Fremd)  (Fremd)  (Fremd)
```

Jeder Hop ist ein Sicherheitsrisiko, eine Latenz, eine Abhängigkeit.

---

## 2. Yakoon ist lokal-first

Yakoon ist anders designed:

```
Terminal / Web-UI / SSH → Yakoon Runtime → Lokale Daten
         (Interface)       (Kernel)       (Eigentum)
```

Die Runtime läuft **dort, wo die Daten sind**:

- **Im Unternehmen** – auf einem Server im LAN, direkt an die Firmen-DB angebunden
- **Auf dem Entwickler-Rechner** – Yakoon kann lokal Files, Postgres, APIs im Netzwerk erreichen
- **Im Rechenzentrum** – aber als eigener Service, nicht als fremde Cloud

Der Web-Client (`y5ncli-web`) ist **nur ein Interface** – genau wie der Console-Client und der SSH-Client. Das Web ist nicht die Plattform. Die Plattform ist die Runtime.

```python
# Yakoon lokal: Zugriff auf alles im Netzwerk
async def run(space):
    data = await space.ports.get(OnSourceRead)(
        query="SELECT * FROM invoices WHERE status = 'open'"
    )
    # Direkter DB-Zugriff, kein API-Gateway, kein SaaS-Zwang
```

---

## 3. Konsequenz für die KI

Die gleiche Frage stellt sich bei KI:

> **Brauchen wir die beste KI für alles, oder lokale KIs für spezielle Aufgaben?**

### Die SaaS-KI (ChatGPT, Claude, Gemini)

- Kann alles – aber kennt deine Daten nicht
- Läuft in einer fremden Cloud – deine Daten verlassen das Unternehmen
- Kostet pro Token – bei vielen internen Abfragen teuer
- Eine Monokultur – ein Modell für alle Domänen

### Die lokale KI (Ollama, LM Studio, lokale Modelle)

- Läuft im Unternehmen – Daten bleiben da
- Spezialisiert pro Domäne – ein kleines Modell für Rechnungen, eins für Projekte
- Kostet Strom, nicht Tokens
- Mehrere Modelle – das passende für jede Aufgabe

In Yakoon sind beide Modelle **nur weitere Akteure** (siehe `docs/KI-ALS-AKTEUR.md`). Der Unterschied:

```
SaaS-KI:                                   Lokale KI:
  ┌─────────────┐                            ┌──────────────┐
  │ GPT-7       │                            │ llama-3-8b   │
  │ Kennt alles │                            │ Kennt deine  │
  │ Kennt dich  │                            │ Rechnungen   │
  │ nicht       │                            │             │
  └──────┬──────┘                            └──────┬───────┘
         │ InputEvent                              │ InputEvent
         ▼                                         ▼
  ┌──────────────────────────────────────────────────────┐
  │                  Yakoon Runtime                       │
  │                                                        │
  │  "invoice list --status=open" → PermissionChecker OK  │
  │  → EntityStore → Projection → Client                  │
  └────────────────────────────────────────────────────────┘
```

**Die Runtime entscheidet, welche KI was tun darf – nicht die KI selbst.**

---

## 4. Was Yakoon lokal kann, was eine Web-App nie kann

| Feature | Web-App (SaaS) | Yakoon (Lokal) |
|---------|---------------|----------------|
| **Dateisystem-Zugriff** | ❌ (Browser-Sandbox) | ✅ `OnSourceRead` für lokale Pfade |
| **Lokale Datenbank** | ❌ (nur via API) | ✅ EntityStore + Postgres im LAN |
| **Interne APIs** | ❌ (CORS, VPN) | ✅ Direkter Zugriff |
| **LDAP/AD-Anbindung** | ❌ (muss proxy) | ✅ Direkt via Port |
| **Kommandozeile** | ❌ | ✅ Console + SSH |
| **Offline-Betrieb** | ❌ (braucht Internet) | ✅ Vollständig ohne Netz |
| **KI lokal** | ❌ (API-Key nötig) | ✅ Ollama / LM Studio |
| **Datenhoheit** | ❌ (Drittanbieter) | ✅ Eigene Infrastruktur |

---

## 5. Das Missverständnis: Web ist nur ein Client

Wenn man `y5ncli-web` sieht, denkt man: "Ah, eine Web-App." Aber das ist ein Irrtum.

```
Was der Benutzer sieht:
  Browser ← → Yakoon Web ← → HTTP/WS ← → Yakoon Server

Was wirklich passiert:
  Browser (Interface)     Yakoon Runtime (Kernel)     Unternehmensdaten
       │                         │                          │
       │   WebSocket            │                          │
       ├─────────────────────────►  OnSourceRead            │
       │   ProjectionEvent       │  ────────────────────────►│
       │◄─────────────────────────┤                          │
       │                         │     Postgres/Datei/API    │
       │                         │◄──────────────────────────┤
```

Der Browser rendert nur. Die Runtime tut. Der Browser kommt an keine Daten – die Runtime schon.

Das Web-Interface ist **genau so limitiert wie das Console-Interface**: es zeigt Projections und schickt InputEvents. **Die Runtime ist das System, nicht das Web.**

---

## 6. Was Yakoon wirklich kann

Weil Yakoon lokal läuft, kann es Dinge, die keine Web-Plattform kann:

```bash
# Auf dem Firmen-Server:
> invoice list --status=open
> ssh connect --host=web01 --command="restart nginx"
> db query "SELECT * FROM logs WHERE level = 'error'"
> backup start --target=/mnt/backup --rotation=30d
> deploy --service=api --version=2.4.1
> incident report --id=INC-2024-042 --include-logs
```

Das sind keine "Web-Anwendungen". Das sind **System-Operationen**. Eine Web-App kann das nur, wenn sie tief in die Infrastruktur integriert ist – dann ist sie aber keine Web-App mehr, sondern ein Runtime-Kernel mit Web-Interface.

Yakoon ist dieser Kernel. Ob das Interface ein Browser, ein Terminal oder ein SSH-Client ist, spielt keine Rolle.

---

## 7. Zusammenfassung

```python
# Zwei Philosophien:

# Web-First:
App = Frontend + Backend + Cloud + API + DB
# Du baust eine Web-Anwendung.
# Deine Daten liegen bei einem Drittanbieter.
# Deine KI auch.

# Yakoon-First:
App = Runtime + Interface
# Die Runtime läuft dort, wo die Daten sind.
# Das Interface kann Web, Terminal, SSH, Desktop sein.
# Die KI kann lokal oder remote sein – die Runtime entscheidet.
# Deine Daten verlassen nie dein Netzwerk.
```

> **Yakoon kann Unternehmen steuern, weil es nah an den Daten ist.**
>
> Ein Web-Interface kann Yakoon nur als Frontend nutzen.
> Aber Yakoon ist nicht das Web-Interface.
> Yakoon ist der Kernel, der das Unternehmen orchestriert.
>
> **Das Web ist ein Client. Die Runtime ist das System.**

---

## 8. Bewertung der lokalen Architektur

### Was überzeugt

Der Web-First-Ansatz hat uns in eine Sackgasse geführt. Jede Firma hat 20 SaaS-Tools, jedes mit eigener Cloud, eigener API, eigenem Auth – und die Daten liegen über 20 Anbieter verstreut. Die KI soll dann "das Unternehmen steuern", aber sie kommt an keine Daten, weil alles hinter 20 APIs liegt.

Yakoon lokal-first ist die **Umkehrung**: Die Runtime sitzt bei den Daten, die Interfaces sind austauschbar. Das ist nicht "grösser denken", das ist **anders denken**.

```python
# Der typische SaaS-Stapel:
Daten → SaaS-API → Cloud → Web-App → Browser
  (fremd)  (fremd)  (fremd)  (fremd)

# Yakoon:
Daten → Yakoon Runtime → Interface (Web/Terminal/SSH)
  (eigen)    (eigen)      (austauschbar)
```

Der Unterschied ist nicht technisch – er ist **strukturell**. Wer kontrolliert die Daten? Wer bestimmt, welche KI darauf zugreift? Wer kann neue Interfaces bauen, ohne die Daten zu migrieren?

### Was nachdenklich macht

Der Web-First-Ansatz hat sich nicht aus Böswilligkeit durchgesetzt, sondern weil er echte Probleme löst:

| Problem | Web-First-Lösung | Yakoon-Lösung |
|---------|-----------------|---------------|
| **Deployment** | `git push` | Firmen-Server einrichten |
| **Updates** | Automatisch (SaaS) | Manuell / eigene Pipeline |
| **Zugriff von unterwegs** | Browser reicht | VPN / Tunnel |
| **Kollaboration** | Eingebaut (geteilte Sessions) | Muss gebaut werden |
| **Benutzer-Onboarding** | Link reicht | Account anlegen + Runtime-Zugriff |

Das sind lösbare Probleme, aber sie sind echter Aufwand, den Web-First-Entwickler nicht sehen.

### Fazit

Die Architektur ist die richtige für das **eigentliche Problem**. Die Frage ist nicht "Web oder lokal". Die Frage ist **"Wer kontrolliert die Daten?"** Und die Antwort ist eindeutig: **Das Unternehmen.** Yakoon lokal-first ist dafür die richtige Antwort.

Der Web-Client ist trotzdem wichtig – nicht als Plattform, sondern als **Tor für den Benutzer**, der nicht im Terminal leben will. Dass das Web nur ein Client ist und die Runtime woanders läuft, ist die einzig saubere Trennung.

> **Die Runtime ist das Produkt. Das Web ist ein Client. Das Terminal ist ein Client. SSH ist ein Client.**
>
> Alles andere folgt daraus.
