# EntityStore Contracts

The EntityStore guarantees the following contracts — independent of backend (Memory, Postgres, ...).

## append & Revisionen

1. **append erzeugt Revision**  
   `append(key, patch={...})` → `put.rev == 1`, `get(key).rev == 1`

2. **append erhöht Revision**  
   `append` × 3 → `put.rev == 3`, `get(key).rev == 3`

3. **get liefert aktuellen Zustand**  
   `append(key, patch={"name": "a"})` + `append(key, patch={"name": "b"})`  
   → `get(key).data["name"] == "b"`

4. **as_of liefert historischen Zustand**  
   `append` bei `t1`, `append` bei `t2`  
   → `get(key, as_of=t1).data == zustand_nach_t1`  
   → `get(key, as_of=t2).data == zustand_nach_t2`

5. **Revisionen bleiben geordnet**  
   3 × `append` → `get(key).rev == 3`, jede Zwischenrevision ist via `as_of` erreichbar.

## Optimistic Concurrency

6. **expected_rev verhindert Konflikte**  
   `append(key, ..., expected_rev=1)` bei aktuellem `rev=2` → `ConcurrencyError`

7. **expected_rev erlaubt korrekten Fortschritt**  
   `append(key, ..., expected_rev=2)` bei aktuellem `rev=2` → Erfolg, `rev=3`

## replace & delete

8. **replace überschreibt vollständig**  
   `append(key, {"a": 1})` + `replace(key, {"b": 2})` → `get(key).data == {"b": 2}`

9. **delete setzt Zustand auf None**  
   `append(key, ...)` + `delete(key)` → `get(key).ok == False`

## Snapshots

10. **Snapshot verändert Ergebnis nicht**  
    100 × `append` (löst periodische Snapshots aus)  
    → `get(key).data == letzter_stand`  
    → alle `as_of`-Aufrufe liefern weiterhin korrete Zwischenstände

## Indexe

11. **scan findet Indexeinträge**  
    `append(key, ..., indexes=[IndexSpec("email", value)])`  
    → `scan(email_key, value) == [key]`

12. **scan nach replace aktualisiert**  
    `append(key, ..., indexes=[...("email", "a")])`  
    `replace(key, ..., indexes=[...("email", "b")])`  
    → `scan("email", "a") == []`  
    → `scan("email", "b") == [key]`

13. **scan nach delete entfernt**  
    `append(key, ..., indexes=[...("email", "a")])`  
    `delete(key)`  
    → `scan("email", "a") == []`

## Backend-Gleichheit

14. **Memory == Postgres**  
    Alle obigen Tests laufen identisch mit beiden Backends.
