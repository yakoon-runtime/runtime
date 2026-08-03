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

- [ ] **D1 — Module loader duplicated**
      `executor/runtime.py:186-218` is byte-identical logic to
      `boot/python/_shared.py:136-178` (`yak.bundle.*` import surgery). The
      engine should reuse the boot helper.
- [ ] **D2 — Token parser triplicated**
      `nodes/request/request.py`, `sources/request.py`, `sdk/libs/models/request.py`
      — same `token()`/`arg()`/`option()` logic (~180 lines). Extract one shared
      base.
- [ ] **D3 — Renderer/compiler constructed twice**
      `wire/runtime.py:91-93` and `build_projector` each build a
      `JinjaRenderEngine`, `PackageReader`, and `Compiler`. Inject one set.
- [ ] **D4 — Small duplicates**
      `Sleep`/`SleepUntil`, `form.py` async/sync mirror, `_empty()`/`_emit_text()`
      helpers, `_norm_value`, three identical `create_store` wirings, duplicated
      `Protocol` declarations (move to `machine/ports.py`).
- [ ] **D5 — Simplify runtime initialization chain**
      the console app calls `host.setup()`, which creates a throwaway session
      (`on_get_session()`) that `setup_nodes()` ignores; the app only needs
      `on_initialize()` (store.initialize + tree.setup). Adapt the console app
      or `RuntimeManager.setup()` so initialization is direct.

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
- [ ] **E3 — Store feature trim**
      `transaction()`, `gc`, historical `at_time`, `FastPatchStrategy`,
      `SnapshotHint.FORCE` are unused by consumers (~400-500 removable lines).
- [ ] **E4 — `flow/policies/` fragmentation + German UI strings**
      one tiny class per file; error messages hardcoded German in an API
      library. Merge into one module; make messages English/parametrized.
- [ ] **E5 — `percept/` in the wrong layer**
      console typewriter animation + profiler live in the runtime API; move to
      the console app.

## F. Ownership First (ADR-10) violations

- [ ] **F1 — Engine interprets `pack:` scheme**
      `nodes/tree.py:473-501` `_make_resolve_handler` parses and imports the
      `pack:` reference in the runtime — belongs to the host.
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
