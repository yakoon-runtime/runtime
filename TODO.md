- su - pw mit Dialog -> Fokus form
- Jobs-flow verwendet derzeit die Platform
- api.* ist auch inden Plugins zu verwenden
- Projection asset -> Hier braucht es ein Dict, damit auch Bilder in der Projekte geladen werden können.

# TODOS:
1. Web Apps reparieren (tote Imports, ~3 Minuten)
2. Security-Lücken (SSH ohne Auth, Postgres Default Creds, SHA-256 ohne Salt)
3. **Collapsible paste in Projection** — Bei Pastes >5 Zeilen den Inhalt in der TextArea als `collapsed=True` markieren, Client zeigt `[N lines inserted]` mit Expand per Enter/Tab/Klick. Nicht UI-Logik, sondern Projection-Protocol: Server steuert, Client rendert passend.
