# EntityStore Contracts

The EntityStore guarantees the following contracts — independent of backend (Memory, Postgres, ...).

## Append & Revisions

1. **append creates a revision**  
   `append(key, patch={...})` → `put.rev == 1`, `get(key).rev == 1`

2. **append increases the revision**  
   `append` × 3 → `put.rev == 3`, `get(key).rev == 3`

3. **get returns the current state**  
   `append(key, patch={"name": "a"})` + `append(key, patch={"name": "b"})`  
   → `get(key).data["name"] == "b"`

4. **as_of returns historical state**  
   `append` at `t1`, `append` at `t2`  
   → `get(key, as_of=t1).data == state_after_t1`  
   → `get(key, as_of=t2).data == state_after_t2`

5. **Revisions remain ordered**  
   3 × `append` → `get(key).rev == 3`, every intermediate revision is reachable via `as_of`.

## Optimistic Concurrency

6. **expected_rev prevents conflicts**  
   `append(key, ..., expected_rev=1)` at current `rev=2` → `ConcurrencyError`

7. **expected_rev allows correct progress**  
   `append(key, ..., expected_rev=2)` at current `rev=2` → success, `rev=3`

## Replace & Delete

8. **replace overwrites completely**  
   `append(key, {"a": 1})` + `replace(key, {"b": 2})` → `get(key).data == {"b": 2}`

9. **delete sets state to None**  
   `append(key, ...)` + `delete(key)` → `get(key).ok == False`

## Snapshots

10. **Snapshot does not change results**  
    100 × `append` (triggers periodic snapshots)  
    → `get(key).data == latest_state`  
    → all `as_of` calls still return correct intermediate states

## Indexes

11. **scan finds index entries**  
    `append(key, ..., indexes=[IndexSpec("email", value)])`  
    → `scan(email_key, value) == [key]`

12. **scan after replace updates**  
    `append(key, ..., indexes=[...("email", "a")])`  
    `replace(key, ..., indexes=[...("email", "b")])`  
    → `scan("email", "a") == []`  
    → `scan("email", "b") == [key]`

13. **scan after delete removes**  
    `append(key, ..., indexes=[...("email", "a")])`  
    `delete(key)`  
    → `scan("email", "a") == []`

## Backend Parity

14. **Memory == Postgres**  
    All tests above run identically with both backends.
