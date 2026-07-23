# y5napp-labs

*Labs, examples, and experimental features for Yakoon.*

This package contains runnable examples that demonstrate the Yakoon
SDK and runtime capabilities. Each lab is a simple `async def main()`
command registered in the workspace tree under `/labs/dsl/`.

## DSL Labs

| Lab | Module | Demonstrates |
|-----|--------|-------------|
| `cmd` | `y5n.apps.labs.dsl.cmd` | Sub-command dispatch |
| `context` | `y5n.apps.labs.dsl.context` | Context, session, request access |
| `delay` | `y5n.apps.labs.dsl.delay` | Timer / sleep |
| `dlg` | `y5n.apps.labs.dsl.dlg` | `io.form()` with dict fields |
| `form` | `y5n.apps.labs.dsl.form` | `io.form()` with typed `Field` models |
| `prompt` | `y5n.apps.labs.dsl.prompt` | `io.prompt()` + `io.receive()` |
| `receive` | `y5n.apps.labs.dsl.receive` | `io.receive()` — sequential input |
| `send` | `y5n.apps.labs.dsl.send` | `io.send()` + `io.receive()` on channel |
| `suspend` | `y5n.apps.labs.dsl.suspend` | Self-suspend and resume via `jobs fg` |
| `ticker` | `y5n.apps.labs.dsl.ticker` | Periodic timer output |
| `write` | `y5n.apps.labs.dsl.write` | `io.write()` output |

## Running

Each lab is accessible via its tree path:

```
/labs/dsl/prompt
/labs/dsl/form
/labs/dsl/suspend
...
```
