# Delete in EntityStore

## Ausgangslage

Der `EntityStore` hat heute keine `delete()`-Methode.

| Operation | Status |
|-----------|--------|
| `append(key, patch)` | Vorhanden |
| `replace(key, doc)` | Vorhanden |
| `get(key)` | Vorhanden |
| `get(key, at_time=...)` | Vorhanden (historisch) |
| `scan(...)` | Vorhanden |
| `gc(...)` | Vorhanden (alte Revisionen/Snapshots) |
| `delete(key)` | **Fehlt** |

Was es auf Patch-Ebene gibt:

```python
# JsonPatchStrategy
def create_delete(*, current, fields) -> JsonValue:
    # erzeugt [{"op": "remove", "path": "/name"}, ...]

# FastPatchStrategy  
def create_delete(*, current, fields) -> JsonValue:
    # erzeugt {"del": ["name", ...]}
```

Das entfernt aber nur **Felder** aus einem Dokument, nicht die Entity selbst.

---

## Ansätze

### A — Hartes Löschen (Physical Delete)

CurrentRow, Revisionen, Snapshots und Index-Einträge werden physisch entfernt.

```
delete(key)
  → CurrentRow löschen
  → Index-Terms für entity_id löschen
  → Revisionen löschen
  → Snapshots löschen
```

**Problem:** `get(key, at_time=gestern)` liefert nichts mehr. Historische Anfragen
brechen. Das widerspricht dem Event-Store-Charakter.
SCD (Slowly Changing Dimension) ist nicht mehr möglich.

**Fazit:** Für einen Event Store nicht geeignet.

---

### B — Tombstone (Soft Delete)

"Löschen" ist ein Event wie jedes andere. Es wird ein spezieller Patch
angewendet, der die Entity auf `data=None` setzt (Tombstone).
Die Historie bleibt erhalten.

```python
class EntityStore:
    async def delete(self, *, key: Key, indexes=(), meta=None, expected_rev=None) -> PutResult:
        patch = self._writer.create_tombstone()
        return await self.append(
            key=key,
            patch=patch,
            indexes=indexes,
            meta=meta,
            expected_rev=expected_rev,
        )
```

**Patch-Strategie:**

```python
# create_tombstone() für FastPatch:
{"tombstone": True}

# für JsonPatch:
[{"op": "replace", "path": "", "value": None}]
```

Nach dem Tombstone:

| Query | Ergebnis |
|-------|----------|
| `get(key)` | `data=None, rev=N` (tombstoned) |
| `get(key, at_time=vor_delete)` | `data={...}, rev=N-1` (rekonstruiert) |
| `scan(...)` | Entity taucht nicht auf (Index-Terms entfernt) |

`GetResult.ok` gibt `False` zurück bei Tombstone.

**Aufwand:**
- `create_tombstone()` in beiden PatchStrategies (~5 LOC)
- `delete()` in EntityStore (~10 LOC)
- Keine Änderung an Backends (reused `append`)
- Index-Terms werden über `indexes=[]` entfernt

---

### C — Tombstone + GC Hard Delete

Wie B, aber `gc()` kann getombstoned Entities nach Ablauf der
`RetentionPolicy` physisch entfernen.

```
gc(policy)
  → Finde Entities, deren Tombstone älter als keep_deleted_days
  → Lösche CurrentRow + Revisionen + Snapshots + Index
```

Dafür bräuchte es einen neuen Parameter in `RetentionPolicy`:
```python
keep_deleted_days: int | None = None  # None = nie hart löschen
```

---

## Empfehlung

**B (Tombstone) als ersten Schritt.**

Begründung:

1. Konsistent mit Event-Store-Prinzip — jedes Delete ist ein Event
2. Historische Queries bleiben möglich
3. Kein neuer Code in Backends (Memory/Postgres) nötig
4. `GetResult.data is None` existiert bereits als Konvention
   (heute für "not found", morgen auch für "tombstoned")

**C (GC Hard Delete) optional später**, wenn physische Bereinigung
wirklich gebraucht wird — z.B. DSGVO/Vergessenwerden.
