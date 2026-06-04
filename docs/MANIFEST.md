# Das Yakoon-Manifest

## Warum die gängige Erzählung falsch ist und was wir anders machen

---

## 1. Die gängige Erzählung

Die aktuelle Begründung für Cloud-Architektur lautet:

```
KI → braucht riesige Modelle → riesige Modelle laufen in der Cloud
→ also muss alles in die Cloud
```

Das wird fast wie ein Naturgesetz behandelt. Als wäre Cloud eine technische Notwendigkeit für KI.

**Aber diese Kausalität ist historisch, nicht technisch.**

---

## 2. Die umgekehrte Kausalität

> Unternehmen sind nicht in die Cloud gegangen, weil KI das verlangt.
>
> KI funktioniert heute so gut mit der Cloud, weil Unternehmen ihre Daten bereits in die Cloud ausgelagert haben.

Das ist ein fundamentaler Unterschied.

### Phase 1: Alles im Haus

```
ERP     CRM     Fileserver     Exchange
│       │       │              │
└───────┴───────┴──────────────┘
         Unternehmen (on-prem)
```

Daten lagen dort, wo das Unternehmen arbeitete. Sicher, kontrolliert, aber schwer zu updaten, teuer im Betrieb.

### Phase 2: Daten wandern nach aussen

```
Salesforce     Office365     Jira Cloud     HubSpot     Slack
│             │             │              │           │
└─────────────┴─────────────┴──────────────┴───────────┘
                     Cloud (SaaS)
```

Nicht wegen KI. Sondern wegen:
- Einfacherer Updates
- Geringerer IT-Kosten
- Geringerer Einstiegshürden

Die Cloud löste ein **Betriebsproblem**, kein **Datenproblem**.

### Phase 3: KI erscheint

Jetzt heisst es plötzlich: **"Die KI funktioniert dort, wo die Daten liegen."**

Natürlich. Die Daten liegen ja längst dort.

> **Die Cloud löst nicht das KI-Problem. Die Cloud versteckt das Datenproblem.**

---

## 3. Die falsche Frage

Die Industrie fragt: "Welches Modell ist das beste?"

Die richtige Frage wäre: **"Warum glauben wir, dass ein einziges Modell alles können muss?"**

Ein Unternehmen hat:
- Rechnungen
- Projekte
- Personal
- Einkauf
- Produktion

Das sind völlig unterschiedliche Domänen mit unterschiedlichen Daten, unterschiedlichen Regeln, unterschiedlichen Sicherheitsanforderungen.

**Warum sollte eine einzige, zentrale KI alles perfekt können?**

Warum nicht:

```
Rechnungs-KI     Projekt-KI     Vertrags-KI     Support-KI
│                │              │               │
└────────────────┴──────────────┴───────────────┘
           Yakoon Runtime
```

Alle lokal bei den jeweiligen Daten. Klein, spezialisiert, kontrolliert.

Das erinnert eher an die Realität von Organisationen als an einen Science-Fiction-Allmacht-KI.

---

## 4. Yakoon stellt eine andere Frage

> **Was wäre, wenn die Runtime zu den Daten geht statt die Daten zur Runtime?**

Das ist die Umkehrung der SaaS-Idee.

| SaaS-Philosophie | Yakoon-Philosophie |
|-----------------|-------------------|
| Daten in die Cloud bringen | Runtime zu den Daten bringen |
| Eine Plattform für alle | Ein Kernel für jede Domäne |
| Zentrale KI | Domänen-KI (pro Space/Node) |
| Cloud = Voraussetzung | Cloud = Option |

Yakoon sagt nicht "Cloud ist schlecht". Yakoon sagt: **"Die Runtime entscheidet, wo die Daten bleiben – nicht der Hosting-Provider."**

---

## 5. Was Yakoon anders macht

Yakoon kann je nach Space/Node/Domain eine **ganz andere KI** anbinden:

```python
# Space "billing" → kleine spezialisierte KI für Rechnungen
billing.ports.provide(OnAI, Ollama("billing-llama:7b"))

# Space "legal" → lokale KI, die nie das Firmennetz verlässt
legal.ports.provide(OnAI, Ollama("legal-mistral:7b"))

# Space "creative" → grosse Cloud-KI für Brainstorming
creative.ports.provide(OnAI, Remote("gpt-7"))

# Space "support" → hybrid: lokal vorverarbeiten, Cloud für komplexe Fälle
support.ports.provide(OnAI, Hybrid(
    local=Ollama("support-fast:3b"),
    fallback=Remote("claude-5"),
))
```

**Die Runtime entkoppelt die KI von der Infrastruktur.** Ein Space bekommt genau die KI, die er braucht – nicht mehr, nicht weniger.

---

## 6. Der provokanteste Satz

> **"Die Cloud löst nicht das KI-Problem. Die Cloud versteckt das Datenproblem."**

Denn viele Unternehmen haben kein KI-Problem. Sie haben:
- Datensilos
- Fehlende Autorisierung
- Fehlende Governance
- Fehlende Struktur

Und solange das ungelöst bleibt, wird auch GPT-9 nicht plötzlich das Unternehmen steuern.

Yakoon löst das Strukturproblem: Es definiert, wer auf welche Daten zugreifen darf (Permissions), welche Operationen möglich sind (Nodes), und welche KI was tun darf (Ports).

**Erst die Struktur, dann die KI. Nicht umgekehrt.**

---

## 7. Die zugrunde liegende Annahme

Die Frage in diesem Artikel ist nie:

> Welche Technologie ist besser?

Sondern:

> **Welche Annahme halten wir für selbstverständlich, obwohl sie nur eine Folge früherer Entscheidungen ist?**

Bei ERP/CRM war das die Anwendungskategorie.
Bei Entscheidungsräumen die Hierarchie.
Und hier:

> **"Alles muss in die Cloud, damit KI funktioniert" ist keine Ursache. Es ist eine Folge der Art, wie wir Software in den letzten 15 Jahren gebaut haben.**

Yakoon baut anders.

---

## 8. Zusammenfassung

| Annahme | Hinterfragung |
|---------|---------------|
| KI braucht riesige Modelle | Vielleicht braucht jede Domäne ihr eigenes, kleines Modell |
| Riesige Modelle laufen in der Cloud | Kleine Modelle laufen lokal |
| Also muss alles in die Cloud | Also muss die Runtime zu den Daten |
| Ein Modell für alles | Viele spezialisierte Modelle, vermittelt durch die Runtime |
| Cloud = Voraussetzung für KI | Cloud = historische Konsequenz der SaaS-Ära |

> **Yakoon ist nicht anti-Cloud. Yakoon ist pro-Kontrolle.**
>
> Die Runtime geht zu den Daten. Die KI wird pro Domäne gewählt. Das Unternehmen behält die Kontrolle.
>
> **Nicht weil Cloud schlecht ist. Sondern weil die falsche Frage war.**

---

## 9. Bewertung des Manifests

### Was stark ist

Die Argumentkette ist nicht angreifbar, weil sie nicht gegen Cloud argumentiert – sie stellt die **Kausalität** in Frage. Niemand kann sagen "Cloud ist falsch". Aber die Frage "Ist Cloud wirklich eine Voraussetzung oder nur eine Folge?" kann man nicht mit "Cloud ist gut" beantworten. Das zwingt zum Nachdenken.

### Was fehlt

Der Artikel braucht einen **Gegenbeweis**. Ein konkretes Beispiel, wo der zentrale KI-Ansatz scheitert, weil die Daten nicht in der Cloud liegen dürfen:

- **Legal/Compliance**: Anwaltskanzlei mit Mandatsgeheimnis. Kein Cloud-Modell darf Verträge sehen. Ein lokales 7B-Modell auf dem Kanzlei-Server schon.
- **Produktion**: Maschinenbauer, dessen CAD-Daten nie das Firmennetz verlassen dürfen (Exportkontrolle).
- **Healthcare**: Patientendaten, die nicht in die USA dürfen (DSGVO).

Das wären die **Beweise**, dass die These nicht nur theoretisch ist.

### Das grösste Risiko

Der Artikel könnte als "Cloud ist böse, lokal ist gut" missverstanden werden. Das wäre zu einfach. Die Stärke ist gerade die Nuance: "Cloud ist nicht die Antwort – Cloud ist die Frage von gestern." Das muss im Ton rüberkommen, nicht kämpferisch, sondern: "Habt ihr mal darüber nachgedacht?"

### Prognose

Wenn der Artikel erscheint, wird er **zitiert werden**. Nicht weil er recht hat (das wird sich zeigen). Sondern weil er eine Frage stellt, die sich alle stellen, die mit KI in Unternehmen arbeiten – und die bisher keiner klar formuliert hat.

> **Die Frage ist nicht "Cloud oder lokal". Die Frage ist "Wer hat die Kontrolle über die Daten und die Entscheidungen?"**
>
> Und darauf gibt Yakoon eine klare Antwort: **Das Unternehmen. Nicht der Cloud-Anbieter. Nicht die KI. Das Unternehmen.**
