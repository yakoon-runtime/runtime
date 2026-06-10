# Test-TODO

## ✅ Alle vier Runtime-Regeln getestet

| Regel | Test | Datei |
|-------|------|-------|
| P1: Error kills Foreground | `test_error_kills_foreground` | `test_foreground.py` |
| P2: Parser — Command + Tokens | `test_start_cmd_parses_tokens` | `test_commands.py` |
| P3: Runner — Kein Foreground → Dispatch | `test_input_without_foreground_dispatches_new_flow` | `test_user_input.py` |
| P3: Runner — Foreground → Push | `test_input_with_foreground_pushes_to_flow` | `test_user_input.py` |
| P4: Scheduler Channel Wake | `test_schedule_waiting_wakes_flow` | `test_channels.py` |
