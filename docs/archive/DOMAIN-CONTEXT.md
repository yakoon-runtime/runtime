> __SUPERSEDED__ by `INTELLIGENT-NODES.md` (2025-06-10)
> Kern-Erkenntnis: Domain Context gehört nicht an den Node,
> sondern wird per Setup im Space installiert.

# Domain Context — Intelligent Nodes

## Problem

Heutige LLM-Integrationen folgen meist diesem Muster:

```
User → LLM → Tools → OS/Git/Files/…
```

Die KI hat Zugriff auf alles. Sicherheit ist reine Prompt-Ebene.
Skalierung bedeutet: mehr Tools, längere Prompts, mehr Halluzination.

## Idee

Yakoon dreht das um:

```
User → Node → Domain-KI → Domain-Port
```

Nicht die KI bedient das System. **Der Node wird intelligent.**

Ein Node bekommt einen `DomainContext`, der beschreibt:

- in welcher Umgebung er lebt (z. B. Fedora, CRM, ERP)
- welche Aktionen er kennt (z. B. `list_processes`, `create_contact`)
- welche Informationen er über seine Domäne hat

Die KI erbt die Fähigkeiten des Nodes. Nicht die Fähigkeiten des Systems.

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

Die KI kann nur das tun, was der Node darf. Ein OS-Node hat
keinen Zugriff auf CRM, Git oder Mail. Er kennt diese Welt nicht.

## Beispiel: OS-Node

```python
os = Node(
    key="os",
    domain=DomainContext(
        metadata={
            "platform": "Fedora",
            "version": "40",
        },
        capabilities=[
            "list_processes",
            "list_files",
            "disk_usage",
            "current_user",
        ],
        prompt_template="Du bist ein OS-Assistent. "
                        "Wähle eine Aktion aus: {capabilities}",
    ),
    permissions=...,   # geerbt vom Parent
    run=os_handler,
)
```

Der Handler nutzt Domain + Ports, nicht die Shell:

```python
async def os_handler(space):
    action = call_llm(space.domain, space.request)
    # action == "list_files"
    result = await space.ports.fs.list("/tmp")
    yield out_text(result)
```

## Komposition

Intelligente Nodes sind komponierbar — genau wie normale Nodes:

```python
files = yield start_cmd("os", "list files in /tmp")
yield start_cmd("archive", files)
```

Das ist **Node → Node**, nicht Node → Shell → Text → nächster Node parst Text.
Aktionen bleiben semantisch, testbar, loggbar, berechtigbar.

## Abgrenzung zu OpenCode

| Aspekt | OpenCode | Yakoon (Vision) |
|--------|----------|-----------------|
| KI-Zugriff | System-weit | Node-Scope |
| Sicherheit | Prompt + Tool-Whitelist | Permission-Hierarchie |
| Skalierung | Über Prompts | Über Domänen |
| Komposition | Text (Stdout/Stdin) | Runtime (Outcome/Channel) |
| Aktionstyp | Shell-Command | Node-Aktion |

## Offene Fragen

- Wer definiert den DomainContext? Node-Autor, Admin, oder zur Laufzeit?
- Darf ein Node mehrere Domänen haben?
- Wie lernt ein Node neue Capabilities?
- Gibt es einen LLM-Node, der als Dienst für andere Nodes fungiert?
- Wie sieht die LLM-Integration aus — eigener Port (`llm.generate`) oder
  direkt im Handler?

## Nächste Schritte (Konzept)

1. DomainContext als Dataclass skizzieren (Feld-Entscheidungen)
2. Einen ersten intelligenten Node definieren (z. B. `os`)
3. Interface zwischen Handler und LLM klären (Port oder Direktaufruf)
4. Komposition zweier intelligenter Nodes als Szenario durchspielen
