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

## Grant-Key-Schema

- Grant-Keys sind **volle Node-Pfade** im Runtime-Baum:
  `/usr/bin/ls`, `/usr/sbin/ident/accounts`, `/opt/crm/contact/edit`.
- Optionaler Action-Suffix: `/opt/crm/contact/edit.version`.
- Die Engine kennt ausschliesslich den Runtime-Baum — kein App/Command-Schema.

## PermissionBits

- Ein einzelnes Bit-Feld pro Grant: `r`, `w`, `x` heute; weitere Bits
  (z.B. `a` administer, `d` delegate) koennen spaeter ergaenzt werden.
- Kein Doppel-`rwx:rwx` (Owner/Group/Other existiert nicht als Achse — die
  Entitaeten Account/Gruppe sind bereits erste Klasse).

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

