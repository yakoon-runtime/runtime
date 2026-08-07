# Experiment: Permissions

Branch: `experiment/permissions`
Status: Experiment — Entscheidungen werden hier konserviert, Produktionsadoption folgt spaeter als ADR.

## Architekturregel

> **Permissions are granted to Accounts on runtime paths.**

## Gesamtkonzept

> **In Yakoon gibt es nur eine Identitaet: den Account.**
> Der Account besitzt optional Profilinformationen. Alles Weitere sind
> Eigenschaften dieser Identitaet.

```text
Account
──────────────────────────────
username
credentials

profile?        ← optional (name, mail, language, avatar)

groups
grants
```

- **Account** ist die einzige Sicherheitsidentitaet: Login, Credentials,
  Gruppen, Grants. Eine Identitaet kann sein: Stefan, Scheduler, API,
  Backup, CRM-Bot — alle sind gleichwertige Identitaeten.
- **Profil** sind optionale Informationen, die ein Mensch zusaetzlich
  besitzt (`name`, `mail`, `language`, `avatar`). Ein Bot hat kein Profil.
  Der Unterschied ist nicht *User vs. Account*, sondern *Account mit Profil*
  vs. *Account ohne Profil*. Der Begriff **User** ist bewusst gestrichen.
- **Group** ist ein Buendel von Accounts, das selbst Grants tragen darf.
- **Join** verbindet Account -> Gruppe (`account_key` als Subject).
- **Grant** setzt auf Account oder Gruppe.

## Pipeline

```text
Account
  ↓
PermissionResolver
  ↓
PermissionSet
  ↓
Elevation
  ↓
Execution
```

Vier Domaenen: **Identity → Authorization → Elevation → Execution**.

Elevation (sudo-aequivalent): Stefan bleibt Stefan. Moechte er eine
Operation auf einem privilegierten Pfad ausfuehren (`users delete peter`),
verlangt das System eine Verifikation — er wird nie `stefan-admin`.
Berechtigung kommt aus der Gruppe, Aktivierung per Verifikation.

> **Elevation aktiviert privilegierte Operationen nach erfolgreicher Verifikation.**

Die Formulierung "Verifikation" ist bewusst offen: heute ein Passwort,
morgen Passkey, FIDO2, MFA, Hardware-Key, Biometrie. Die Architektur
schreibt kein Secret fest, sondern eine Verifikation.

## Effective Permissions

```text
EffectivePermissions(Account) =
    grants(Account)
  ∪ grants(Gruppen, denen der Account angehoert)
```

Gelost vom `PermissionResolver` beim Login; Ergebnis landet per
`session.set_permissions()` auf der Session.

## Pfad-Vererbung (Invariante)

> **Permissions are inherited along the runtime path hierarchy.**

- Ein Grant auf `/usr/bin` gilt fuer `/usr/bin` und **alle Nachfahren**
  (segmentbasiert: `/usr/bin/ls` ja, `/usr/binary` nein). Keine Wildcards noetig.
- Die Mount-Struktur des Runtime-Baums wird dadurch zum Sicherheitsmodell:
  ein Pack waehlt mit seinem Mount-Pfad, wo es lebt — und dort werden Rechte
  vergeben (`admins → /usr/bin`, `ident-admins → /usr/sbin/ident`).
- Allow-Bits **addieren sich** entlang der Kette, Deny-Bits werden **subtrahiert**.
  `effective = union(allow) - union(deny)`. Ein deny entfernt nur seine Bits —
  ein generellerer allow bleibt Basis. Kein "most specific wins".
- **Durchquerung (Traversal) — abgeleitet, nicht vergeben:** Ancestor-
  Container eines expliziten Grants sind automatisch erreichbar. Aus
  `allow /usr/bin` folgt `/, /usr -> r (derived)`. Drei Regeln:
  1. **Grants definieren fachliche Berechtigungen.**
  2. **Traversal wird aus expliziten Grants automatisch abgeleitet** — ein
     explizit erlaubter Bereich ist IMMER erreichbar.
  3. **Ancestor-Denies wirken nur auf fachliche Rechte, niemals auf die
     abgeleitete Erreichbarkeit eines explizit erlaubten Zieles.** Ein
     `deny /usr|r` sperrt `/usr` als Ziel und `/usr/sbin`, aber nicht den
     Weg zu `/usr/bin`. Ein Self-Grant wird nur durch Self-Denies reduziert.
  Trennt **Autorisierung** ("Darf ich?") von **Erreichbarkeit**
  ("Wie komme ich dorthin?").

## Grant-Key-Schema

- Grant-Keys sind **volle Node-Pfade** im Runtime-Baum:
  `/usr/bin/ls`, `/usr/sbin/ident/accounts`, `/opt/crm/contact/edit`.
- Optionaler Action-Suffix: `/opt/crm/contact/edit.version`.
- Die Engine kennt ausschliesslich den Runtime-Baum — kein App/Command-Schema.

## PermissionBits

> **Permissions gelten fuer Runtime-Ressourcen, nicht nur fuer Commands.**

- Ein einzelnes Bit-Feld pro Grant: `r`, `w`, `x` heute; weitere Bits
  (z.B. `a` administer, `d` delegate) koennen spaeter ergaenzt werden.
- Kein Doppel-`rwx:rwx` (Owner/Group/Other existiert nicht als Achse — die
  Entitaeten Account/Gruppe sind bereits erste Klasse).
- **Die Bits beschreiben die Operationen, die auf einem Knoten moeglich sind —
  nicht den Typ des Knotens.** Ein Command nutzt heute fast nur `x`; eine
  Datei morgen `rw`; ein Dokument uebermorgen `rwad`. Der Runtime-Baum wird
  mehr als ein Command-Baum: Commands, Dateien, Dokumente, Datenbanken, APIs,
  Queues, Modelle — alles sind Knoten mit denselben Bits.

## Zwei Ebenen: Runtime-Operationen und Bits

> **Operationen der Runtime und Bits sind getrennt. Der Node-Typ bildet die
> Runtime-Operationen auf die Bits ab.**

Es gibt zwei Ebenen, die nicht verwechselt werden duerfen:

1. **Operationen der Runtime:** `discover`, `read`, `write`, `execute` —
   benannt nach dem, was der Nutzer tut (`cd` ist *discover*, nicht
   *execute*).
2. **Bits:** `r`, `w`, `x` — das kleine, stabile Permission-Vokabular.

Der **Node-Typ** (Container, Command, Document, API, Queue, DB) mappt
Runtime-Operationen auf Bits:

```text
Container  DISCOVER -> r   (sehen + sich bewegen)
Command    READ -> r, EXECUTE -> x
Document   READ -> r, WRITE -> w
API        EXECUTE -> x
Queue      READ -> r, WRITE -> w
Datenbank  READ -> r, WRITE -> w
```

- `cd` fragt nicht direkt "brauche ich r?" — es fragt
  `check(path, DISCOVER)`, und der Container sagt `DISCOVER -> r`.
- Dadurch bleibt das Permission-System klein (`rwx`), waehrend die Runtime
  beliebig wachsen kann — neue Node-Typen mappen nur neu, sie brauchen keine
  neuen Bits.
- **Kein Unix-Kopieren:** `x` auf Verzeichnissen ist ein historischer
  Kompromiss (search/traverse zweckentfremdet). Wir leiten die Semantik sauber
  her: `cd`/`ls`/`man`/`cat` sind Leseoperationen (`discover`/`read`),
  `edit`/`rm`/`mkdir` sind `write`, Command-Ausfuehrung ist `execute`.
- **Bewusste Entscheidung (2026-08-07):** `rwx` wird NICHT auf `x` reduziert.
  Die Bits sind das allgemeine Operationsmodell der Runtime und wachsen mit
  dem System — bei jedem neuen Ressourcentyp keine neuen Sonderregeln.

## Node-Typ via navigable (bestehendes Modell)

Der Node-Typ-Marker existiert bereits: `navigable` in der yak.yml
(`tree.py` liest es, `find_navigable()`/`find_resolvable()` nutzen es).

```text
navigable: true   → Container (Folder)   → DISCOVER -> r
navigable: false  → Eintrag (Leaf)
                     Command    → READ -> r, EXECUTE -> x
                     Document   → READ -> r, WRITE -> w
                     API        → EXECUTE -> x
                     Queue/DB   → READ -> r, WRITE -> w
```

> **Navigation ist eine Runtime-Operation.** `cd` und `ls` sind keine
> Sonderfaelle der Shell, sondern Operationen auf einem Container-Knoten.
> Ob sie erlaubt sind, entscheidet der Permission-Check anhand der Operation
> (`DISCOVER` bzw. `LIST`) und der vom Node-Typ definierten Abbildung auf die
> Bits. In einem Baum mit Dateien/Dokumenten/DBs ist Navigation selbst Teil
> des Permission-Modells, kein Bypass. (Ersetzt die fruehere
> "Visibility/filesystem"-Formulierung.)

Noch offen: Der Permission-Check kennt den Node-Typ noch nicht — `cd`/`ls`
greifen heute ohne `check(DISCOVER)`. Der Anschluss
(Operation -> Bit via navigable) ist der naechste Schritt.

## allow / deny

- **Deny bleibt** (Decision 2026-08-06). `deny`-Grants subtrahieren Bits,
  ermoeglicht gezielten Ausschluss einzelner Accounts aus Gruppen-Rechten
  ohne Membership-Aenderung. Fail-Closed-Standard.
- **Deny subtrahiert nur seine Bits** (Decision 2026-08-07): ein
  `deny /usr/bin/shutdown|x` entfernt nur `x` vom ererbten
  `allow /usr/bin|rwx` — `r`/`w` bleiben. Kein "most specific wins".
- Drei Command-Typen: **public** (`anonymous: true`), **normal**
  (`anonymous: false, privileged: false`), **gefaehrlich**
  (`privileged: true` → Elevation noetig).

## Trennung Engine / Ident

- Die Engine fragt nur: *"Darf dieser Account diesen Pfad mit dieser Operation
  benutzen?"* — `check(account, path, EXECUTE)`.
- Woher die Berechtigungen kommen (direkt, Gruppe, Rolle) ist ausschliesslich
  Sache des Ident-Packs.
- Der `PermissionChecker` kennt keine Ident-Interna.

## Umsetzungsstand

- [x] Grant-Key-Schema: volle Node-Pfade, single `bits`, deny behalten
- [x] Engine-fq: `InvocationResolver` baut Pfad-Keys via `node.path`
- [x] Join auf Account -> Gruppe umgestellt (Modell, Service, Commands, Index)
- [x] Account vervollstaendigt: Namespace, Index, Service, publish, Demo-Daten
- [x] PermissionResolver account-basiert verdrahtet + publiziert
      (`ident.permissions.resolver`), liefert Spec-Strings
- [x] Auth-Fluss: su/authenticate -> Resolver -> `session.set_permissions()`
      (neuer `SessionAdapter.set_permissions`, parse-t Spec-Strings -> PermissionSet)
- [x] grants-Commands auf Account umgestellt (`grants account add/remove/show`)
- [x] Bootstrap auf Pfad-Schema + Root-Account
- [x] anonymous-Flag: Tree liest `anonymous` aus yak.yml (default False).
      `su`/`logout`/`err` deklarieren es explizit. Alle anderen Knoten sind
      jetzt permission-pflichtig.
- [x] Experiment-Test `tests/test_permissions_experiment.py`: bootstrap ->
      resolver -> parser -> set (direkt, Gruppe, deny-Subtraktion).
- [x] **User-Konzept gestrichen**: `AccountData` traegt optionale Profil-Felder
      (`name`, `mail`, `language`); `UserData`/`UserService`/user-Namespace
      entfernt; `users`-Commands wurden zu `accounts`-Commands
      (`add/list/edit/delete` mit `--name/--mail/--language`);
      `joins users` wurde `joins accounts`.
- [x] **Pfad-Vererbung**: `PermissionSet.check` laeuft die Pfadkette nach oben,
      allow-Bits addieren sich, deny-Bits subtrahieren. Bootstrap-Grants auf den
      realen Baum (`/usr/bin`, `/usr/sbin/ident`, `/opt`, `/dsl`). 9 Tests in
      `test_permission_set.py`, Gesamtlauf 238 gruen.
- [x] **Grant-Vokabular**: `permission_key` → `path`. Ein Grant ist
      `path + bits + deny` — der Administrator vergibt Zugriff auf einen
      Runtime-Pfad, nicht auf eine abstrakte Permission. `grants perm show`
      wurde `grants path show`.
- [x] **Invocation-Fix**: grant-yak.yml zeigen `add NAME PATH`, show nutzt nur
      noch `name` (fehlerhafter `permission`-Param entfernt).
- [x] **`rwx` als Operationsmodell bestaetigt**: nicht auf `x` reduziert —
      Permissions gelten fuer Runtime-Ressourcen (Commands, Dateien, Docs,
      DBs, APIs, Queues), Bits = Operationen am Knoten.
- [x] **Zwei Ebenen definiert**: Runtime-Operationen (discover/read/write/
      execute) vs. Bits (rwx); Node-Typ bildet ab. Node-Typ-Marker ist
      bereits `navigable` in der yak.yml.
- [x] **Operation-Klasse**: `Operation(READ, WRITE, EXECUTE)` — bewusst nur
      drei Operationen; `cd`/`ls`/`man`/`cat` sind alle READ (kein
      DISCOVER/LIST-Sonderweg). `Node.required_bit(operation)` mappt
      via `navigable` (Container: READ->r/WRITE->w; Leaf: READ->r/
      EXECUTE->x). `PermissionChecker.check(session, node, operation)` und
      `InvocationResolver` pruefen EXECUTE ueber Node+Operation statt
      perm_key-String. Tests: `test_operations.py`.
- [x] **cd/ls als READ-Operation**: neuer `permissions`-Port
      (`PermissionAdapter.check(path, operation)`) — Commands fragen in
      Operationen statt Bits. `cd` verweigert `Access denied` ohne READ auf
      den Ziel-Container; `ls` filtert Eintraege ohne READ. Nur Runtime-Knoten
      sind geschuetzt — reine Dateisystem-Mounts (z.B. ~/home) bleiben frei.
      Tests: `test_permission_adapter.py`, `test_checker_wire.py`.
- [x] **Root-Grant `/\|rwx`**: root/admins bekommt den hierarchisch hoechsten
      Grant. Vererbung deckt den ganzen Baum — root ist root, weil sein Grant
      ganz oben beginnt. Kein Superuser-Flag, kein Bypass: dieselbe Mechanik
      wie fuer jeden Account. `ls /` zeigt wieder alle Mounts.
- [x] **Durchquerung**: Pfad zu den eigenen Rechten ist automatisch lesbar
      (Traversal im `PermissionSet`, segmentbasiert). Stefan mit Grant auf
      `/usr/bin` sieht `/usr` und `/` beim `ls`, aber `/usr/sbin`/`/opt`
      nicht. Tests: `test_permission_set.py` (5 neue).
- [ ] **Elevation**: privilegierte Pfade verlangen Verifikation, auch wenn der
      Account die Berechtigung hat. (Design: Policy vs. Pfad-Deklaration — offen)
- [ ] End-to-End auf Prozessebene: echte su-Session -> PermissionDenied sichtbar

## Verhaltenswechsel (Experiment)

Vorher baute der Tree jeden Knoten als `anonymous=True` — der Permission-Check
war in der echten Runtime toter Code. Jetzt ist jeder Knoten permission-pflichtig
sofern er nicht `anonymous: true` deklariert. Das macht den Check real wirksam.

## Noch offene Fragen

- Prozesstraennung: Resolver liefert Spec-Strings, Engine parst — bewusst so,
  damit kein Engine-Objekt ueber die stdio/JSON-Grenze wandert.
- Elevation-Semantik: wann/wo wird die Verifikation eingeholt? (am Engine-Dispatch
  vs. im Command via `su --as-admin`-Stil). Noch zu entscheiden.
- `privileged: true` in der yak.yml ist **noch nicht endgültig**: moeglicherweise
  ist Elevation eher eine **Policy-Entscheidung** als eine Pfad-Deklaration. Die
  Runtime sollte nur wissen, dass ein Pfad *Elevation verlangen kann*; ob sie
  tatsaechlich verlangt wird, koennte eine Security Policy entscheiden.

