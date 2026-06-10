# Intelligent Nodes — KI als Resolver, nicht als Akteur

> Konsolidiert aus `DEMO-ARCH.md` und `DOMAIN-CONTEXT.md`.
> Ersetzt beide Dokumente.

## Problem

Klassische LLM-Integrationen folgen diesem Muster:

```
User → LLM → Tools → OS/Git/Files/…
```

Die KI hat Zugriff auf alles. Sicherheit ist reine Prompt-Ebene.
Skalierung bedeutet: mehr Tools, längere Prompts, mehr Halluzination.

Die erste Idee war, eine KI über `start_task(...)` Shell-Kommandos
erzeugen zu lassen — ähnlich wie OpenCode. Dabei entstand die Frage:

> Wie verhindern wir, dass eine KI beliebige Kommandos ausführt?

## Lösung: KI ist Resolver, nicht Akteur

Yakoon betrachtet KI nicht als "Gehirn" des Systems.

Die KI **löst Sprache in Bedeutung auf**. Danach übernimmt die Runtime.

```
"zeige alle Prozesse"
↓
list_processes
↓
Port: OnRunProcess.run("ps", ["aux"])
```

```
KI interpretiert
Runtime handelt
```

Nicht:

```
KI entscheidet
Runtime führt aus
```

Diese Trennung ist entscheidend für Berechtigungen, Auditing,
Tests, Komposition und Unternehmenssicherheit.

## Permission-Kette

Heute:

```
User
└─ Permission
   └─ Node
```

Morgen:

```
User
└─ Permission
   └─ Node
      └─ KI (ererbt Scope des Nodes)
```

Die KI besitzt keine eigenen Rechte. Sie erbt die Fähigkeiten
des Nodes. Ein Benutzer ohne Zugriff auf den Node `os` besitzt
automatisch keinen Zugriff auf dessen KI.

## Der Node als Domäne

Der Benutzer denkt in Domänen, nicht in Shell-Kommandos:

```
os mail crm office git
```

Nicht:

```
ls ps du find grep
```

Der Node kennt seine Welt:

```
OS:
- Fedora 42
- verfügbare Aktionen: list_files, list_processes, disk_usage
- verfügbare Ports
```

Die KI arbeitet ausschließlich innerhalb dieser Domäne.
Sie kennt weder CRM noch Mail noch Git.

## OpenCode vs. Yakoon

| Aspekt | OpenCode | Yakoon |
|--------|----------|--------|
| KI-Zugriff | System-weit | Node-Scope |
| Sicherheit | Prompt + Tool-Whitelist | Permission-Hierarchie |
| Skalierung | Über Prompts | Über Domänen |
| Komposition | Text (Stdout/Stdin) | Runtime (Outcome/Channel) |
| Aktionstyp | Shell-Command | Node-Aktion |
| KI-Rolle | Entscheider | Resolver |

## Domain Context

Der Domain Context gehört **nicht an den Node**. Die Runtime
soll weiterhin möglichst klein bleiben.

Statt:

```python
Node(domain=DomainContext(...))
```

Setzt ein Space per **Setup** sein Domänenwissen:

```python
# y5nspace-os/setup.py
space.ident("os")
space.grant("user", "list_files", "list_processes", "disk_usage")
```

Der Kontext wird Teil des Spaces, nicht der Runtime-Ontologie.
(Ähnlich wie `space-ident`, `membership`, `grant`.)

## Shell als Adapter

Die Shell ist keine Domäne. Sie ist ein technischer Adapter.

Vergleich:

```
identity ≠ ldap
mail ≠ smtp
os ≠ shell
```

Deshalb:

```
OS-Space
└─ Shell Port
```

Nicht:

```
Shell-Space
```

## Space-Struktur (Vorschlag)

```
y5nspace-os/

runtime/
    setup.py    # Grants, Permissions, Domain-Wissen
    space.py    # Space-Definition
    os.py       # Handler + Action-Dispatch
```

Bewusst noch keine Zerlegung in `files.py`, `network.py`,
`system.py` — das erfolgt erst, wenn die Domäne wächst.

## V1: Pragmatische Blacklist

Für die ersten Demos genügt eine einfache Blacklist als
Übergang. Ziel ist nicht Unternehmenssicherheit, sondern
Schutz der Entwickler-Workstation.

**Verboten:**

```
rm sudo su passwd shutdown reboot
systemctl curl wget scp ssh
```

**Erlaubt (nur lesend):**

```
ls find ps pwd whoami df du free
uname cat head tail
```

Die Blacklist wird obsolet in dem Moment, wo der OS-Space
keine Shell-Kommandos mehr exposed, sondern nur noch
semantische Aktionen (`list_files`, `list_processes`, …).

## Komposition

Das langfristige Ziel:

```python
files = yield start_cmd('os "zeige Dateien in /tmp"')
yield start_cmd("archive", files)
```

**Node → Node**, nicht Shell → Text → Shell → Text.
Die Runtime bleibt semantisch.

## Langfristige Vision

```
y5nspace-os
y5nspace-mail
y5nspace-office
y5nspace-git
y5nspace-crm
```

Jeder Space besitzt:

- eigene Permissions
- eigenes Domänenwissen
- eigene KI (als Resolver)
- eigene Ports
- eigene Sicherheitsregeln

Die KI wird nicht systemweit intelligent.
**Der Node wird intelligent.**

Das ist der zentrale Unterschied zur klassischen Agenten-Architektur.
