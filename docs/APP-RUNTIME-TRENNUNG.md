# App/Runtime-Trennung + Discovery

## Ziel

Texture und Runtime werden sauber getrennt. Texture ist ein reiner Client,
der sich mit einer oder mehreren Runtimes verbindet. Die Runtime läuft
unabhängig — Texture startet sie nicht.

## TODO

### 1. texture.yaml

Texture braucht eine Konfigurationsdatei `texture.yaml` (neben der Binary
oder in `~/.config/y5n/`), die eine Liste von Standard-Runtimes enthält:

```yaml
runtimes:
  - name: local
    url: ws://localhost:9100
    default: true
```

Beim Start verbindet Texture alle Runtimes aus der Config als Tabs. Ohne
Config: leerer Start mit Hinweis ("Keine Runtime konfiguriert. /connect
<url> oder texture.yaml anlegen.").

- `texture.yaml` existiert nicht → leerer Start, `/connect` möglich
- `texture.yaml` existiert → Tabs für jede Runtime aus der Config

### 2. Texture startet keine Runtime mehr

`on_mount` ruft nicht mehr `_add_local_tab()` auf. Stattdessen lädt es
die Config und verbindet die konfigurierten Runtimes.

Der Benutzer startet Runtime und Texture getrennt:

```bash
python scripts/serve-runtime.py 9100    # Terminal 1
python scripts/serve-texture.py          # Terminal 2
```

oder per `texture.yaml` mit `runtime.local.start` (optionaler Befehl).

### 3. /connect bleibt in Texture

`/connect <url>` und `/disconnect` sind weiterhin Texture-Kommandos.
Texture besitzt die Verbindungen (Tabs, WebSockets).

### 4. runtime discover (optional, nächster Schritt)

Die Runtime bekommt ein neues Space/Feature: Auflisten bekannter Runtimes.

```text
runtime discover
→ office (ws://10.0.0.5:9100)
→ production (ws://10.0.0.8:9100)
```

Texture kann das Ergebnis nutzen, um einen "Connect"-Dialog anzubieten.
Die Discovery selbst (mDNS, Registry, manuelle Config) ist Zukunft.

---

## Was bleibt

- Tab-Bar, Tabs, `/connect`, `/disconnect` — alles in Texture
- Runtime kennt keine UI, kein Texture
- Texture startet keine Runtime (außer optional per Config-Action)

---

## Was sich verschiebt (später, nicht jetzt)

- Runtime-to-Runtime Kommunikation ("start flow on office")
- Runtime Federation
- Discovery-Mechanismen (mDNS, Registry)
