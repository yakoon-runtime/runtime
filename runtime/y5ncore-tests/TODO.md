# Test-TODO

## Offene Runtime-Regeln (ohne Tests)

### P1: Error kills Foreground ✅

- `test_error_kills_foreground` in `test_foreground.py`
- Foreground-Flow wirft Exception → Scheduler killt den Flow und räumt Fokus
- `scheduler.py:204-207`

### P2: Parser — Command + Tokens

- `start_cmd("ls -la --color", channel=ch)` → `cmd="ls"`, `tokens=["-la", "--color"]`
- Sub-Flow bekommt die Tokens

### P3: Runner — Kein Foreground → Input startet neuen Flow

- `session.foreground_flow is None` + User Input → `on_dispatch` statt `push_event`
- Zweite Hälfte der USER_INPUT-Regel (nur Foreground-Fall getestet)

### P4: Scheduler Channel Wake

- `_schedule_waiting` weckt wartende Flows bei neuem Mail auf SESSION-Channel
- Funktioniert implizit, nie explizit getestet

## Gewünschte Tests (niedrige Priorität)

- `test_foreground_switch` ✅
- `test_multiple_session_receivers` ✅
- `test_multiple_commands_parallel` ✅
- `test_multiple_tasks_parallel` ✅
