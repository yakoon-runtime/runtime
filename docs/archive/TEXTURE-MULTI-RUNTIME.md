# Texture Multi-Runtime

## Vision

Texture wird vom Terminal für eine Runtime zum **Browser für ein Runtime-Netzwerk**.
Der Benutzer sieht all seine Runtimes, verbindet sich parallel und arbeitet in Spaces,
ohne wissen zu müssen wo die Runtime läuft (lokal/remote/cloud).

## Plan

### Step 1 — Texture: Multi-Tab

Texture erweitern, sodass mehrere Websocket-Verbindungen parallel möglich sind.

- Jede Verbindung = ein Tab
- Tabs sind nebeneinander sichtbar (z.B. als Reiter oben)
- Jeder Tab hat eigene Input/Output-Historie
- Eingabe wird an die aktive Runtime gesendet
- `/connect <url>` — neuen Tab öffnen
- `/disconnect` — aktiven Tab schließen

**Dateien:** `texture/` (Frontend + Backend der texture-app)

### Step 2 — Zwei lokale Runtimes testen

Auf demselben Rechner zwei Runtime-Instanzen mit verschiedenen Ports starten.

```
Runtime A: Port 9100, Spaces: shell, os
Runtime B: Port 9101, Spaces: demo, wetter
```

Texture mit `/connect ws://localhost:9101` verbinden und zwischen
den Tabs wechseln. Prüfen: fühlt sich das natürlich an?

**Dateien:** Konfiguration/Startskripte, keine Code-Änderung an der Runtime.

### Step 3 — Runtime verteilen

Eine Runtime auf einem zweiten Rechner starten (Raspi, Server, Docker-Container).
Texture verbindet sich remote.

- Runtime-Konfiguration ohne UI (Headless-Modus)
- Texture verbindet via `ws://<ip>:<port>`
- Test: OS-Agent läuft lokal, anderer Agent (z.B. Docker-Status) läuft remote

### Step 4 — Runtime Discovery (Zukunft)

`connect` ohne Parameter zeigt verfügbare Runtimes im Netzwerk.
Z.B. via mDNS/Bonjour oder einer Registry.

---

## Offene Fragen

- Wie unterscheiden sich Tabs visuell? (Farbe/Icon pro Runtime?)
- Soll ein Tab eine Standard-Runtime sein (z.B. localhost)?
- Wie verhalten sich Flows, die über mehrere Runtimes gehen? (Erstmal nicht.)
- Teilen sich Tabs den Session-State? (Erstmal nicht — jede Runtime eigene Session.)
