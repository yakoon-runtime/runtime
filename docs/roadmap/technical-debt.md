# Technical Debt — Runtime

> Working list of technical debt, correctness issues, and simplification
> opportunities in `runtime/`. Reviewed 2026-08-03.
> Each section is independently committable. Priority: A → G.

## A. Correctness bugs

- [x] **A1 — Dispatcher drops patch operations**
      `engine/document/transport/dispatcher.py:286` — `ops = ops[:BATCH_SIZE]`
      truncates the publishable batch without requeueing the tail. Clients never
      finish rendering blocks that exceed the batch. Fix: requeue the remainder
      or emit everything.
- [x] **A2 — `system:projection` registered eight times**
      `engine/wire/runtime.py:246-294` — every registration overwrites the
      previous exports; `unregister()` removes only the last set.
- [x] **A3 — Postgres store snapshots are no-ops**
      `store/event/backends/postgres/postgres.py:254-258` —
      `load_snapshot_at_or_before`/`write_snapshot` do nothing; the store
      believes snapshots are persisted but they never are. Every append
      triggers `on_write_snapshot`. Fix or remove the snapshot feature.
- [x] **A4 — TOCTOU race in `store.append()`**
      `store/event/store.py:118-143` — default (non-transactional) path reads
      current rev, checks `expected_rev`, then upserts. `transaction()` is used
      by nobody, so the intended protection is absent. Serialize writes per key
      or route the default path through a transaction.
- [x] **A5 — `sequence/wire.py` imports asyncpg unconditionally**
      `store/sequence/wire.py:5` — memory backend breaks without the optional
      postgres dependency. Lazy-import like `event/wire.py`.

## B. Host naming collision

- [x] **B1 — `RuntimeHost` vs ADR-10 host**
      `machine/manager.py` — the session manager class shared the word "host"
      with the ADR-10 component host (three distinct meanings across the
      engine). Renamed to `RuntimeManager`, file `host.py` → `manager.py`,
      adapters use `manager` instead of reaching into private `_host`.

## C. Dead code

- [x] **C1 — `flow/port.py` imports a nonexistent module**
      `api/flow/port.py:3` — would crash on import; nothing uses it. Delete.
- [x] **C2 — `contracts/` duplicates the runtime protocols**
      `api/contracts/*` — ~150 lines, imported by nobody, a second definition of
      `Call`/`Response`/`Register`/`Context`. Delete or unify.
- [x] **C3 — Executor kinds other than `RUNTIME` are dead**
      `executor/{python,script,process,dotnet}.py` — `executor:` is declared
      nowhere in the tree; `dotnet.py` only raises. Keep `RuntimeExecutor`,
      delete the unused kinds plus the `.yak/run/` and `.yak/<phase>/app.py`
      fallbacks and `health()`/`DiagnosticExecutor`.
- [x] **C4 — Dead setup path**
      `machine/engine.py:43-57`, `wire/machine.py:224-236`, `flow/cursor.py`
      — `node.setup` is never assigned; `CommandEngine.setup()`,
      `setup_nodes()`, and the `"setup"` handler path are unreachable. Remove.
      (The live `RuntimeManager.setup()` → `on_initialize` chain that the
      console app calls was kept.)
- [x] **C5 — `devtools/` broken import**
      `runtime/devtools/__init__.py:2` imports `.prompt`, which does not exist.
      Delete the package (unreferenced) or fix it.
- [x] **C6 — Other dead symbols**
      `settings/ai.py` (whole file), `percept/profiler.py`,
      `values/secret_value.py` (+ the whole `values/` package), `naming/resolver.py`,
      empty `host/`, `_DocumentHeader`/`Intent` (`document/model/header.py`),
      `DocumentEvent.is_final()`, `NodeNotRunnable`, dead `__post_init__` in
      `flow/primitives/effect.py`, `build_index()` stub
      (`wire/runtime.py:216`), duplicate themes (`ONE_DARK`==`ATOM_DARK`,
      `CATPPUCCIN`==`CATPPUCCIN_MOCHA`).

## D. Duplication

- [x] **D1 — Module loader duplicated**
      `executor/runtime.py` and `nodes/tree.py` both did the same
      `rpartition` + importlib + getattr dance for `pack:` references.
      Extracted one shared `PackReference` bootstrap linker
      (`engine/bootstrap.py`), used by the runtime executor and the tree's
      resolve-handler builder. Single source for the `pack:` bootstrap link.
- [x] **D2 — Token parser triplicated**
      `nodes/request/request.py`, `sources/request.py`, `sdk/libs/models/request.py`
      — same `token()`/`arg()`/`option()` logic (~180 lines). Extract one shared
      base. Done: shared `TokenQuery` base in `api/tokens.py`; the API `Request`
      and the SDK `Request` subclass it, `DataRequest` delegates to it.
- [x] **D3 — Renderer/compiler constructed twice**
      `wire/runtime.py:91-93` and `build_projector` each build a
      `JinjaRenderEngine`, `PackageReader`, and `Compiler`. Done: one wire-level
      assembly (`build_document_stack`) builds the full pipeline once and
      returns it as a `DocumentStack`; `build_runtime` consumes it.
- [x] **D4 — Small duplicates**
      `Sleep`/`SleepUntil` (SleepUntil is now a subclass of Sleep),
      `form.py` async/sync mirror (one sync field-lifecycle generator,
      driven by the async wrapper), `_empty()` helpers (one `empty_flow()`
      in `engine/flow/util.py`), three identical `create_store` wirings
      (one `create_entity_store()` factory in the store), duplicated
      `Protocol` declarations (true duplicates moved to
      `machine/ports.py`). `_norm_value` was left as-is: the memory
      backend validates types, the postgres backend coerces — intentional
      difference, not a duplicate.
- [x] **D5 — Simplify runtime initialization chain**
      the console app calls `host.setup()`, which created a throwaway session
      (`on_get_session()`) that `setup_nodes()` ignored. `RuntimeManager.setup()`
      now calls `on_setup()` directly; the app only needs
      `on_initialize()` (store.initialize + tree.setup).

## E. Over-engineering

- [ ] **E1 — Dual document model**
      compiler builds dicts, API builds `Inline*` dataclasses, hand-written
      decoder bridges them; `error_kind` drift (`core.py` allows only
      `validation`/`system`); `normalize()` + `_blocks_to_dict` build the same
      shell; `gc.collect()` workaround; broken `ImageResolver`. Pick one
      representation (derive from `yds-v1.yaml`).
- [ ] **E2 — Dispatcher rewrite**
      `document/transport/dispatcher.py` 367 → ~150 lines: stack-based traversal
      instead of recursion, delete the dead partition logic and the 8-protocol
      port layer.
- [x] **E3 — Store feature trim**
      Removed: `transaction()`/`begin_transaction` (StoreRuntime, wires,
      backend `transaction()` methods, `MemoryTransactionScope`),
      `gc`/`gc_global` (EntityStore, backends, protocols),
      `SnapshotHint.FORCE`, the always-on `_enable_revisions` toggle, and
      their now-unused imports.
      Kept: historical `get(at_time)` — a tested, working feature that the
      engine's `OnGet` protocol already declares; and `FastPatchStrategy` —
      a complete, unwired alternative patch format (`PatchFormat.FASTPATCH`
      exists in the model) kept as a future option for switching the flat-entity
      write path. Revisit either when a consumer needs it.
- [ ] **E4 — `flow/policies/` fragmentation + German UI strings**
      one tiny class per file; error messages hardcoded German in an API
      library. Merge into one module; make messages English/parametrized.
- [x] **E5 — `percept/` in the wrong layer**
      Closed as by design: the typewriter animation is shared infrastructure —
      it will be used by both the console and the future `texture` app, so it
      belongs in the runtime API, not in one app.

## F. Ownership First (ADR-10) boundaries

- [x] **F1 — Engine interprets `pack:` scheme**
      Resolved as a **bootstrap exception**, not an ownership violation (ADR-10,
      "Bootstrap linking"): before a host can interpret references, the first
      host itself must be loaded. The runtime performs a minimal, mechanical
      linking step for the `entry.run` and `resolve` declarations of host nodes
      only — it loads the declared function, it does not understand it. All
      later references (`resources:`, `ports:`, a command's `entry.run`) are
      host-interpreted. The single bootstrap linker is `engine/bootstrap.py`
      (`PackReference`), shared with the runtime executor.
- [ ] **F2 — Engine rewrites host requests**
      `nodes/tree.py:425-470` `_make_host_handler` builds the
      `Request`/`NodeSpace` rewrite in the runtime.

## G. Hygiene

- [ ] **G1 — German comments** violate AGENTS.md (all comments in English):
      `machine/engine.py`, `machine/scheduler.py`, `machine/parser.py`,
      `document/compiler/tokens.py`, `store/event/store.py`,
      `document/model/header.py`.
- [ ] **G2 — `print()` instead of logging** (`wire/machine.py:83`,
      `runtime/bus/session_bus.py:48`).
- [ ] **G3 — Small fixes** "Mountes" typo (3 files), `NodeSpace` `None`
      type-ignores (`nodes/tree.py:287-293`).

## H. Parked ideas

- **A host is just a node with a job** — if a host were an ordinary node
  (`async def main()` + SDK), the runtime would only say `await host.run()` and
  the host would use the same runtime services as any component. Its two
  capabilities (execute / resolve) would be offered via ports, not methods.
  This dissolves the last special treatment of hosts. Parked: first resolve the
  rest of this list, then revisit — likely after D2–D5 and E.
