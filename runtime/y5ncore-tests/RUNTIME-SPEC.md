# Runtime-Spezifikation

## FOREGROUND

- Genau ein Flow besitzt den Fokus (Foreground)
- USER_INPUT wird ausschließlich an den Foreground-Flow zugestellt
- Der Foreground-Flow kann jederzeit Background-Flows starten

## BACKGROUND

- Background-Flows erhalten keinen USER_INPUT
- Background-Flows können weiterhin FLOW- und SESSION-Events empfangen
- Wenn der Foreground-Flow endet, bleiben Background-Flows aktiv

## USER_INPUT

- `receive()` ohne Argumente wartet auf USER_INPUT
- Nur der Foreground-Flow empfängt User Input (siehe FOREGROUND)
- User Input wird per `send_user_input` zugestellt

## FLOW

- Flow-lokale Channel sind vom anderen Flow isoliert
- Gleicher Channel-Name in verschiedenen Flows = verschiedene Mailboxen
- `receive("form")` → Scope.FLOW

## SESSION

- Session-übergreifende Channel
- Zwei Flows können über `Scope.SESSION` kommunizieren
- `send()` + `receive(..., scope=Scope.SESSION)`

## COMMANDS

- `start_cmd` dispatched einen Sub-Flow (non-blocking)
- Das Ergebnis (Projection) landet auf dem angegebenen SESSION-Channel
- Der Caller empfängt per `receive(ch, scope=Scope.SESSION)`

## TASKS

- `start_task` dispatched einen OS-Prozess (non-blocking)
- Das Ergebnis (Returncode/Stdout/Stderr) landet auf dem angegebenen Channel
- Integration-Tests starten echte Prozesse

## SUSPEND

- `Suspend()` macht einen Flow nicht runnable
- Ein suspendierter Flow bleibt blockiert, bis er vom Jobsystem wieder aktiviert wird
- Der Flow wird im Scheduler nicht weiter bearbeitet

## STOP

- `Stop` beendet den Flow
- Der Flow wird aus der Session entfernt
- Kein Completion-Event auf dem out_channel
