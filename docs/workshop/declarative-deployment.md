# Workshop — Declarative Deployment

**Branch:** `experiment/deployment`
**Frage:** Wie entsteht aus einer Menge deklarativer Packs eine lauffähige Installation?

> This is a workshop document, not an ADR. It collects the current state,
> the target picture, and the decisions that have to be made before the
> assembler (`yak`) is built. The outcome becomes an ADR once the
> decisions are made.

## 1. Ausgangslage (IST)

### Was eine Installation heute ist

Eine Installation ist eine Verzeichnisstruktur mit Packs (`structure/`)
und einer Runtime-Config (`yakoon-runtime.yml`):

```
structure/
    crm/            → pack with structure/.yak/yak.yml
    worlds/
    ident/
    system/
yakoon-runtime.yml  → listen, workspace_path, known (no stores)
```

### Was an Persistenz heute existiert

| Baustein | Datei | Inhalt | Verdrahtet? |
|---|---|---|---|
| Engine-Default | `StorageSettings` | `backend: memory`, DSN `yakoon_dev` | ja (Runtime-Bau) |
| Engine-Default | `SequenceSettings` | `backend: memory`, DSN `yakoon_sequence` | ja (Runtime-Bau) |
| Space-Config | `docs/config/spaces/contacts.yml` | `storage: postgres` → `yakoon_contacts` | **nein** |
| Space-Config | `docs/config/spaces/worlds.yml` | `storage: postgres` → `yakoon_contacts` | **nein** |
| Space-Loader | `resolve_space_config(space)` | sucht `~/.config/yakoon/spaces/<space>.yml` | ja, als Funktion |
| Pack-Settings | `contacts/settings`, `worlds/settings` | `Settings.load()` liest Space-Config | **nein** (nie aufgerufen) |

**Kernfakt:** Die Space-Configs sind der Vorläufer des Assemblers — aber sie
sind **unverdrahtet**. Kein Pack lädt sie tatsächlich beim Lauf. Persistenz
läuft heute über Engine-Defaults (`memory`), nicht über die Configs.

### Was das bedeutet

Die Kette von heute ist konzeptionell schon fast richtig:

```
Pack → docs/config/spaces/*.yml → Runtime
```

aber die Mitte ist von Hand gepflegt, nach Pack benannt (nicht nach
logischem Store), nicht versioniert/versioniert verwechselt, und nicht
verdrahtet. Zwei Packs (contacts, worlds) teilen sich zufällig dieselbe DB
(`yakoon_contacts`).

## 2. Zielbild

### Heute

```
Pack
    │
    ▼
docs/config/spaces/*.yml      (manuell)
    │
    ▼
Runtime
```

### Morgen

```
Pack                              (deklarativ: stores: [crm])
    │
    ▼
yak                                (der Assembler)
    │
    ▼
Installation                       (Deployment: stores: crm: backend: postgres)
    │
    ▼
Runtime
```

`yak install crm` → Pack lesen → Bedarf sammeln → Deployment erzeugen.

## 3. Verantwortlichkeiten

| Rolle | Was sie tut | Beispiel |
|---|---|---|
| **Pack** | beschreibt Bedarf | `stores: [contacts]` |
| **yak** | assembliert den Bedarf zur Installation | fragt Backend/Instanz ab, erzeugt Deployment |
| **Runtime** | führt aus, stellt Mechanismen bereit | baut Store-Service aus dem Deployment |
| **SDK** | minimale API | `sdk.store("contacts")` |

Das Muster in allgemeiner Form:

```
Beschreiben → Assemblieren → Ausführen → Benutzen
Pack        → yak         → Runtime  → SDK
```

## 4. Entscheidungsfragen

### Stores

- **Q1.** Welche logischen Stores benötigt eine Installation? → Antwort
  heute: `StoreCollector` über alle installierten Packs (ADR-18). `yak`
  übernimmt diese Aufgabe beim Installieren.

### Angelpunkt — ist ein logischer Store global eindeutig?

**Zwei Achsen, keine eine:**

| Achse | Antwort |
|---|---|
| **Bedeutung des Namens** | global — `contacts` = `contacts` überall (wie ein Portname) |
| **Berechtigung des Zugriffs** | pack-lokal — ein Pack kann nur deklarierte Stores nutzen |

**Schärfung der Regel:** Capability-Namen sind global eindeutig. **Aber jedes
Pack muss explizit deklarieren, welche Capabilities es nutzt.** `stores:`
ist eine Dependency-Liste — "wovon hängt dieses Pack ab", nicht "was
existiert".

**Konsequenz (Durchsetzung):** `sdk.store("contacts")` aus einem Pack, das
`stores: [contacts]` nicht deklariert, wirft eine Exception (nicht deklarierte
Abhängigkeit) — wie ein `import`, dessen Modul nicht in den Dependencies
steht. Der Resolver prüft: *liegt der Name in den deklarierten Stores des
Nodes?*

Beispiele:

```yaml
# Reporting hängt von CRM + Telemetrie ab
stores:
  - crm
  - telemetry
```

```yaml
# Migration orchestriert zwischen CRM und Legacy
stores:
  - crm
  - legacy
```

Zwei Packs mit `stores: [contacts]` teilen sich den globalen Store `contacts`
(Kollision = bewusstes Teilen), aber keines kann auf einen **nicht
deklarierten** Store zugreifen.

### Mapping

- **Q2.** Existiert bereits eine physische Datenbank für einen logischen
  Store? → **yak errät nichts.** Es sucht keine Datenbanken, kennt keine
  Namenskonventionen. Es führt den Administrator durch die Zuordnung:
  *"Neue Datenbank"* oder *"Bestehende verwenden"* — dann *"welche?"*.
- **Q3.** Dürfen mehrere logische Stores auf dieselbe physische DB zeigen?
  → **Ja.** Das Zielmodell ist Hybrid (Modell C): das Deployment entscheidet,
  welche logischen Stores auf welche physischen Ressourcen zeigen. `contacts` +
  `ident` → `postgres-main`, `telemetry` → `analytics`. Beliebig viele
  logische Stores pro physischer Ressource, beliebig viele Ressourcen.

**Kernsatz:** **Store ≠ Datenbank.** Der logische Store bleibt `contacts`; die
physische Realität heißt `postgres-main` (eine *Deployment*/*Instance*).
Die Zuordnung ist ausschließlich Aufgabe des Deployments.

### Backend

- **Q4.** Welche Backends gibt es (postgres, sqlite, memory)? Wer kennt die
  Liste — `yak`, das Deployment, oder beide?

### Credentials

- **Q5.** Wo liegen Benutzer und Passwort? → Four Layers (ADR-18): Secret
  Store, nie im Pack, nie im Deployment. Wie verweist das Deployment darauf?

### Migrationen

- **Q6.** Wann werden Migrationen ausgeführt? Beim ersten `install`, beim
  `update`, beim Start der Runtime? Wer besitzt die Migrationslogik — das
  Pack oder das Deployment?

### Updates & Entfernen

- **Q7.** Ein neues Pack kommt hinzu. Was passiert mit bestehenden Stores?
  (nichts — nur neue Stores werden angelegt?)
- **Q8.** Ein Pack wird deinstalliert. Bleibt die physische Datenbank
  erhalten? (Vermutung: ja — Daten gehören nicht dem Pack.)

## Hypothesen des Workshops (Zwischenstand)

1. **Store ist immer logisch.** Das Pack kennt nur Namen.
2. **Mehrere logische Stores dürfen auf dieselbe physische Datenbank
   zeigen.** Store ≠ Datenbank.
3. **Die physische Zuordnung ist ausschließlich Aufgabe des Deployments.**
4. **`yak` errät nichts** — es führt den Administrator durch die
   Zuordnung (neue/bestehende Ressource, welche).
5. **Capability-Namen sind global eindeutig** — aber der Zugriff ist
   pack-lokal: ein Pack kann nur deklarierte Stores nutzen. `stores:` ist
   eine Dependency-Liste (wie Ports / Import-Deklarationen).
6. **Nicht deklarierte Abhängigkeiten sind Fehler** — `sdk.store("x")`
   ohne `x` in `stores:` wirft eine Exception.

## 5. Ergebnis — wer besitzt welche Datei?

Noch offen. Die Antwort bestimmt das Deployment-Modell:

| Datei | Gehört heute | Gehört morgen |
|---|---|---|
| `pack/yak.yml` (`stores:`) | Pack | Pack |
| `docs/config/spaces/*.yml` | Handgepflegt, unverdrahtet | wird ersetzt |
| Installation (Deployment) | — | `yak` (generiert, nicht versioniert) |
| Secret Store | — | Plattform (Keychain/Vault) |
| `yakoon-runtime.yml` | Runtime | Runtime (nur Runtime-Dinge: listen, ports) |

## Nächste Schritte

1. Entscheidungen Q1–Q8 im Workshop festhalten.
2. Das Deployment-Modell als ADR-19 formulieren.
3. Dann: `yak` als Assembler bauen (Installationsdialog, Deployment,
   Provisionierung).
