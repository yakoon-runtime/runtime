# Warum Yakoon Ports? – Was DI allein nicht löst

## Dependency Injection vs. Yakoon Ports

---

## 1. Zwei Richtungen statt einer

Dependency Injection ist **top-down**: der Container hat alles, Konsumenten ziehen sich raus.

```python
# DI: nur eine Richtung
container.bind(Db, postgres)
handler = Handler(db=container.get(Db))
```

Yakoon braucht **zwei Richtungen**:

```python
# ↓ Nach unten delegieren (wer du bist, bestimmt was du darfst)
root.ports.provide(OnSourceRead, ds.read)

# ↑ Nach oben exportieren (Plugin sagt: "Ich kann das")
space.ports.publish(Namespaces, my_namespace_service)
```

Ein Space wie `y5nspace-ident` muss nicht nur Dinge *empfangen*, sondern auch Dinge *anbieten* – dem Eltern-Node seine Identitäts-Dienste zur Verfügung stellen.

In DI müsste der Eltern-Node vorher wissen, welche Dienste das Kind anbietet und alles manuell verdrahten. Yakoon erlaubt **selbstorganisierende Exporte** – ein Space sagt: "Ich bin fertig initialisiert, hier sind meine Capabilities für euch da oben."

---

## 2. Autorität ist an Position gebunden, nicht an Typ

In DI bekommt ein Service, was er braucht, weil er es deklariert (`@inject`). Die Position im System ist irrelevant.

In Yakoon bestimmt die **Position im Baum**, was du sehen kannst:

```
Root (OnProjectionResolve, OnSourceRead, OnCompile, ...)
  └─ system (sieht alles vom Root)
      └─ ls (sieht alles von system + Root)
  └─ runtime (sieht alles vom Root)
      └─ version (sieht alles von runtime + Root, aber NICHT system/ls)
```

Ein tiefer Node im `ident`-Space kann nicht einfach `OnSourceRead` aus dem Root-Space nutzen – er muss im Subtree sein, der unter Root gemountet ist. **Autorität wird durch Hierarchieposition vererbt, nicht durch Import-Deklaration.**

Ein `@inject`-Dekorator gibt dir keinen Kontext darüber, *wo* im System dieser Code läuft. Yakoon sagt: "Du bist Node X unter Parent Y – also hast du Zugriff auf Z, aber nicht auf W."

---

## 3. Subtree-Autonomie (Composition without Coordination)

DI erfordert zentrale Koordination: irgendwo muss ein `WireModule()`, `AppModule` oder `CompositionRoot` stehen, das **alle** Abhängigkeiten kennt.

```python
# DI: zentrale Koordination
class AppModule:
    def configure(self, container):
        container.bind(Projector, ...)
        container.bind(Store, ...)
        container.bind(UserService, ...)  # Root muss Ident-Service kennen!
        container.bind(GroupService, ...) # Root muss Ident-Service kennen!
```

Yakoon erlaubt **unabhängig entwickelte Subtrees**, die sich selbst versorgen:

```python
# Space-Wiring (unabhängig entwickelt in y5nspace-ident)
async def setup(space):
    store = EntityStore(...)
    space.ports.provide(UserService, UserService(store))
    space.ports.provide(Namespaces, Namespaces())

# Root-Wiring (koordiniert nur das Mounten, kein Detailwissen)
platform.mount(shell_space)
platform.mount(ident_space)    # weiss nicht, was ident intern macht
platform.mount(runtime_space)  # weiss nicht, was runtime intern macht
```

Der Root muss nicht wissen, was `y5nspace-ident` intern braucht oder anbietet. Er mountet den Space, und der Space organisiert sich selbst. **Das ist ungefähr so, als würde man ein Linux-Modul laden – es registriert sich selbst, ohne dass der Kernel jede Funktion einzeln verdrahten muss.**

---

## 4. Capability Security (was du nicht hast, kannst du nicht rufen)

DI löst das Problem "wie kriege ich meine Abhängigkeiten?" – aber nicht das Problem "wie verhindere ich, dass unautorisierter Code an sensible Dienste kommt?"

Ein klassisches DI-Framework gibt dir entweder:

- **Globalen Container** → jeder kann alles kriegen (Ambient Authority)
- **Scoped Container** → aber die Scope-Grenzen sind orthogonal zur Geschäftslogik

Yakoon hat mit dem `PermissionChecker` und der hierarchischen Sichtbarkeit einen **eingebauten Autorisierungsmechanismus**:

```python
# node.py: Position bestimmt Sichtbarkeit
class Node:
    ports: NodePorts       # meine Capabilities
    parent: Node | None    # mein Kontext im Baum
    children: dict[str, Node]  # meine Sub-Nodes
```

- Ein Node in `runtime/labs` sieht andere Capabilities als ein Node in `ident/admin`
- Selbst wenn Code `ports.get()` aufruft, wird die Capability nur gefunden, wenn die Container-Kette sie liefert
- `fork()` und `mount()` ziehen explizite Grenzen

DI-Frameworks (Guice, Spring, Castle Windsor, etc.) geben dir entweder alles oder nichts – sie haben kein Konzept von **Capability Scopes, die an eine Baumposition gebunden sind**. Ein Service in Spring bekommt seine Dependencies unabhängig davon, *wo* im Request-Graphen er aufgerufen wird.

---

## 5. Keine zentrale Dependency-Wire-Orgie

In klassischen DI-Systemen wächst der `WireModule` / `AppModule` / `CompositionRoot` mit jeder neuen Komponente. Alles muss zentral bekannt sein.

```python
# Typischer DI-Composition-Root (wächst mit jedem Feature)
wire = [
    Projector, Compiler, Normalizer,
    UserService, GroupService, MembershipService,
    PermissionService, AuditService, DiscoveryService,
    ShellService, RuntimeService, WelcomeService,
    EntityStore, MemoryBackend, PostgresBackend,
    ...
]
```

Yakoon verteilt das Wiring auf die Spaces:

```python
# runtime.py (Root-Wiring) – nur 9 Zeilen Binding
platform.ports.provide(OnSourceRead, ds.read)
platform.ports.provide(OnSessionSave, session_manager.save)
platform.ports.provide(OnAuthorizeRead, perm_checker.can_read)
platform.ports.provide(OnAuthorizeWrite, perm_checker.can_write)
platform.ports.provide(OnProjectionResolve, projector.project)
platform.ports.provide(OnResourceLoad, package_reader.get_text)
platform.ports.provide(OnJinjaRender, jinja_engine.render_str)
platform.ports.provide(OnCompile, compiler.compile)
platform.ports.provide(OnErrorResolve, error_resolve)

# shell/setup.py (Space-Wiring) – völlig eigenständig
space.ports.provide(OnManualResolve, manual_resolver)

# ident/setup.py (Space-Wiring) – völlig eigenständig
space.ports.provide(UserService, UserService(store))
space.ports.provide(GroupService, GroupService(store))
space.ports.publish(OnAuthenticate, authenticator.authenticate)
```

**Jeder Space ist sein eigener Composition Root.** Der Root muss nicht wissen, dass der Shell-Space einen `OnManualResolve` braucht oder dass `y5nspace-ident` einen `UserService` anbietet. Der Space kümmert sich selbst darum.

---

## 6. Dynamische Plugin-Architektur

DI-Systeme sind meist **statisch zur Startzeit konfiguriert**. Du sagst: "Diese 5 Module sind verdrahtet."

Yakoon erlaubt **dynamisches Laden von Subtrees**:

```python
# Ein Space kann zur Laufzeit einen Subtree mounten
shell_node.mount(new_space)

# Oder Capabilities nachträglich bereitstellen
node.ports.provide(NewService, my_service)
```

Weil `fork()` eine Eltern-Kette etabliert, sehen neue Nodes automatisch die bestehenden Capabilities. Der neue Subtree muss nicht ins zentrale Wiring aufgenommen werden – er wird einfach eingehängt.

---

## Zusammenfassung

| Problem | Dependency Injection | Yakoon Ports |
|---------|-------------------|--------------|
| **Richtung** | Nur top-down | `provide` ↓ + `publish` ↑ |
| **Autorität** | Deklariert (`@inject`) | Position im Baum |
| **Subtree-Autonomie** | Zentrale Koordination nötig | Self-wiring Spaces |
| **Zugriffskontrolle** | Alles oder nichts | Hierarchisch abgestuft |
| **Composition** | Alles im Root bekannt | Dezentrales Wiring |
| **Dynamik** | Meist statisch zur Startzeit | Laufzeit-Mounten möglich |
| **Plugins** | Müssen im Root registriert sein | Melden sich selbst an |
| **Metapher** | "Hier sind deine Abhängigkeiten" | "Hier ist, wofür du autorisiert bist" |
